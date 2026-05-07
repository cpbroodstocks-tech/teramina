# pylint: disable=broad-except

import logging
import numpy as np

logger = logging.getLogger("teramina")

try:
    from prophet import Prophet
    import pandas as pd
    _PROPHET_AVAILABLE = True
except ImportError:
    _PROPHET_AVAILABLE = False


class ProphetForecast:

    @staticmethod
    def forecast_abw(abw_samples: list, target_doc: int, current_doc: int) -> dict | None:
        """
        abw_samples: [{"doc": 7, "abw": 2.1}, {"doc": 14, "abw": 3.8}, ...]
        target_doc: DOC to forecast up to
        current_doc: current DOC of cycle

        Returns:
        {
            "docs": [current_doc+1, ..., target_doc],
            "abw_forecast": [...],
            "abw_lower_80": [...],
            "abw_upper_80": [...],
            "model_info": {"r_squared": float, "sample_count": int}
        }
        Returns None if insufficient data (< 4 samples) or if prophet not installed.
        """
        if not _PROPHET_AVAILABLE:
            logger.warning("Prophet is not installed; cannot generate Prophet ABW forecast")
            return None

        if len(abw_samples) < 4:
            logger.debug("ProphetForecast: only %d samples, need 4", len(abw_samples))
            return None

        try:
            origin = pd.Timestamp("2020-01-01")

            df = pd.DataFrame([
                {
                    "ds": origin + pd.Timedelta(days=int(s["doc"])),
                    "y": float(s["abw"]),
                }
                for s in abw_samples
                if s.get("doc") is not None and s.get("abw") is not None
            ])

            if len(df) < 4:
                return None

            model = Prophet(
                growth="linear",
                interval_width=0.80,
                daily_seasonality=False,
                weekly_seasonality=False,
                yearly_seasonality=False,
            )
            model.fit(df)

            future_docs = list(range(current_doc + 1, target_doc + 1))
            future_df = pd.DataFrame({
                "ds": [origin + pd.Timedelta(days=d) for d in future_docs]
            })

            forecast = model.predict(future_df)

            abw_forecast = forecast["yhat"].round(4).tolist()
            abw_lower_80 = np.maximum(forecast["yhat_lower"], 0).round(4).tolist()
            abw_upper_80 = forecast["yhat_upper"].round(4).tolist()

            # Compute R² on training data
            train_forecast = model.predict(df[["ds"]])
            y_true = df["y"].values
            y_pred = train_forecast["yhat"].values
            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

            return {
                "docs": future_docs,
                "abw_forecast": abw_forecast,
                "abw_lower_80": abw_lower_80,
                "abw_upper_80": abw_upper_80,
                "model_info": {
                    "r_squared": round(r_squared, 4),
                    "sample_count": len(df),
                },
            }
        except Exception as exc:
            logger.warning("ProphetForecast.forecast_abw failed: %s", exc)
            return None

    @staticmethod
    def should_use_prophet(abw_samples: list, current_doc: int) -> bool:
        """Returns True if Prophet is appropriate:
        - At least 4 ABW samples available
        - current_doc >= 15 (enough growth history)
        - Samples span at least 14 DOC range
        """
        if len(abw_samples) < 4:
            return False
        if current_doc < 15:
            return False
        docs = [s["doc"] for s in abw_samples if s.get("doc") is not None]
        if not docs or (max(docs) - min(docs)) < 14:
            return False
        return True
