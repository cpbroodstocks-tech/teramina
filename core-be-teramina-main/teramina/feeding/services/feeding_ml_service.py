# pylint: disable=broad-except, too-many-locals, too-many-branches, too-many-statements

import logging
import pickle
from datetime import datetime

import numpy as np

logger = logging.getLogger("teramina")

try:
    import xgboost as xgb
    _XGBOOST_AVAILABLE = True
except Exception:
    xgb = None
    _XGBOOST_AVAILABLE = False

try:
    import shap as _shap_module
    _SHAP_AVAILABLE = True
except Exception:
    _shap_module = None
    _SHAP_AVAILABLE = False

from teramina.cycle.models.cycle_model import Cycle
from teramina.cycle_data.models.cycle_data_model import CycleData
from teramina.feeding.models.feed_realization_model import FeedRealization
from teramina.feeding.models.feeding_ml_model import FeedingModelArtifact
from teramina.pond.models.pond_model import Pond
from teramina.helpers.constant_value import Constant

# DOC threshold for Layer 3 activation
ML_DOC_MIN = 60
# Minimum data points required to extract features
MIN_DATA_POINTS = 10
# Typical target ABW growth rate (g/day) used as simple linear growth curve baseline
ABW_GROWTH_RATE = 0.20  # g/day — conservative linear default


FEATURE_NAMES = [
    "doc",
    "doc_normalized",
    "abw_current",
    "abw_target_at_doc",
    "abw_gap",
    "adg_last_7d",
    "sr_estimate",
    "biomass_kg",
    "do_avg_3d",
    "temp_avg_3d",
    "nh3_avg_3d",
    "do_stress_days_7d",
    "nh3_stress_days_7d",
    "fcr_current",
    "leftover_ratio_avg_3d",
    "pond_size_m2",
    "stocking_density",
]


def _linear_abw_target(doc: int) -> float:
    """Simple linear growth curve: w0=0.1g at DOC 1, grows at ABW_GROWTH_RATE g/day."""
    return 0.1 + ABW_GROWTH_RATE * doc


class FeedingMLService:

    @staticmethod
    def extract_features(cycle_id: str, doc: int):
        """Extract ML features for a specific cycle at a specific DOC.

        Returns a dict of features, or None if insufficient data.
        """
        try:
            cycle_data = CycleData.objects(cycle_id=cycle_id).first()
            if not cycle_data or not cycle_data.result_data:
                return None

            data = cycle_data.result_data
            # Only use data up to and including this doc
            data_up_to = [r for r in data if r.get("doc") is not None and r.get("doc") <= doc]
            if len(data_up_to) < MIN_DATA_POINTS:
                return None

            data_sorted = sorted(data_up_to, key=lambda x: x["doc"])

            # --- ABW ---
            abw_rows = [(r["doc"], r["abw"]) for r in data_sorted if r.get("abw")]
            abw_current = abw_rows[-1][1] if abw_rows else None

            # --- ABW target from simple linear growth curve ---
            abw_target_at_doc = _linear_abw_target(doc)

            # --- ABW gap ---
            abw_gap = (abw_current - abw_target_at_doc) if abw_current is not None else 0.0

            # --- ADG last 7 days ---
            abw_7d = [(d, w) for d, w in abw_rows if d >= doc - 7]
            adg_last_7d = 0.0
            if len(abw_7d) >= 2:
                abw_7d_sorted = sorted(abw_7d, key=lambda x: x[0])
                delta_w = abw_7d_sorted[-1][1] - abw_7d_sorted[0][1]
                delta_d = abw_7d_sorted[-1][0] - abw_7d_sorted[0][0]
                adg_last_7d = delta_w / delta_d if delta_d > 0 else 0.0

            # --- Survival rate and biomass ---
            cycle = Cycle.objects(id=cycle_id).first()
            pond = None
            pond_size_m2 = None
            initial_population = None
            stocking_density = None

            if cycle:
                pond = Pond.objects(id=cycle.pond_id).first()
                if pond:
                    pond_size_m2 = pond.size

            # Try to read initial_stocking from first result_data row
            first_row = data_sorted[0] if data_sorted else {}
            initial_population = first_row.get("initial_stocking") or first_row.get("population")
            if initial_population is None:
                # Fallback: look for any row with initial_stocking
                for r in data_sorted:
                    if r.get("initial_stocking"):
                        initial_population = r["initial_stocking"]
                        break

            # Latest population estimate from result_data
            pop_rows = [(r["doc"], r["population"]) for r in data_sorted if r.get("population")]
            latest_population = pop_rows[-1][1] if pop_rows else None

            sr_estimate = None
            if latest_population is not None and initial_population:
                sr_estimate = min(100.0, (latest_population / initial_population) * 100.0)
            else:
                sr_estimate = 80.0  # conservative default

            biomass_kg = None
            if abw_current is not None and initial_population:
                biomass_kg = abw_current * (sr_estimate / 100.0) * initial_population / 1000.0

            if pond_size_m2 and initial_population:
                stocking_density = initial_population / pond_size_m2

            # --- Water quality 3-day averages ---
            recent_3d = [r for r in data_sorted if r.get("doc") is not None and r["doc"] >= doc - 2]
            do_vals = [r["do_avg"] for r in recent_3d if r.get("do_avg") is not None]
            temp_vals = [r["temp_avg"] for r in recent_3d if r.get("temp_avg") is not None]
            nh3_vals = [r["nh3"] for r in recent_3d if r.get("nh3") is not None]

            do_avg_3d = float(np.mean(do_vals)) if do_vals else 5.0
            temp_avg_3d = float(np.mean(temp_vals)) if temp_vals else 28.0
            nh3_avg_3d = float(np.mean(nh3_vals)) if nh3_vals else 0.0

            # --- Stress days last 7 days ---
            last_7d = [r for r in data_sorted if r.get("doc") is not None and r["doc"] >= doc - 6]
            do_stress_days_7d = sum(
                1 for r in last_7d if r.get("do_avg") is not None and r["do_avg"] < Constant.DO_OPTIMAL_MIN
            )
            nh3_stress_days_7d = sum(
                1 for r in last_7d if r.get("nh3") is not None and r["nh3"] > Constant.NH3_OPTIMAL_MAX
            )

            # --- FCR ---
            total_feed_given = sum(r.get("feed_given_kg", 0) or 0 for r in data_sorted)
            fcr_current = None
            if biomass_kg and biomass_kg > 0 and total_feed_given > 0:
                fcr_current = total_feed_given / biomass_kg

            # --- Leftover ratio 3-day average ---
            leftover_records = FeedRealization.objects(
                cycle_id=cycle_id,
                doc__gte=max(1, doc - 2),
                doc__lte=doc,
            ).only("feed_given", "feed_leftover")
            leftover_ratios = []
            for rec in leftover_records:
                if rec.feed_given and rec.feed_given > 0:
                    leftover_ratios.append((rec.feed_leftover or 0) / rec.feed_given)
            leftover_ratio_avg_3d = float(np.mean(leftover_ratios)) if leftover_ratios else 0.0

            features = {
                "doc": float(doc),
                "doc_normalized": doc / 120.0,
                "abw_current": float(abw_current) if abw_current is not None else 0.0,
                "abw_target_at_doc": float(abw_target_at_doc),
                "abw_gap": float(abw_gap),
                "adg_last_7d": float(adg_last_7d),
                "sr_estimate": float(sr_estimate),
                "biomass_kg": float(biomass_kg) if biomass_kg is not None else 0.0,
                "do_avg_3d": float(do_avg_3d),
                "temp_avg_3d": float(temp_avg_3d),
                "nh3_avg_3d": float(nh3_avg_3d),
                "do_stress_days_7d": float(do_stress_days_7d),
                "nh3_stress_days_7d": float(nh3_stress_days_7d),
                "fcr_current": float(fcr_current) if fcr_current is not None else 0.0,
                "leftover_ratio_avg_3d": float(leftover_ratio_avg_3d),
                "pond_size_m2": float(pond_size_m2) if pond_size_m2 is not None else 0.0,
                "stocking_density": float(stocking_density) if stocking_density is not None else 0.0,
            }
            return features

        except Exception as exc:
            logger.warning("Feature extraction failed for cycle %s DOC %s: %s", cycle_id, doc, exc)
            return None

    @staticmethod
    def predict(cycle_id: str, doc: int):
        """Get ML recommendation.

        Returns dict with recommended_kg, confidence, shap_explanation, model_version,
        or None if ML cannot run.
        """
        if not _XGBOOST_AVAILABLE:
            return None
        if doc < ML_DOC_MIN:
            return None

        try:
            artifact = FeedingModelArtifact.objects(is_active=True).first()
            if not artifact or not artifact.model_bytes:
                return None

            features = FeedingMLService.extract_features(cycle_id, doc)
            if features is None:
                return None

            model = pickle.loads(bytes(artifact.model_bytes))
            feature_names = artifact.feature_names or FEATURE_NAMES
            features_array = np.array(
                [features.get(f, 0.0) for f in feature_names], dtype=float
            ).reshape(1, -1)

            predicted = float(model.predict(features_array)[0])
            predicted = max(0.0, round(predicted, 2))

            # Confidence: use model r2 as proxy, clamp to [0, 1]
            r2 = (artifact.metrics or {}).get("r2", 0.5)
            confidence = float(max(0.0, min(1.0, r2)))

            shap_explanation = FeedingMLService.get_shap_explanation(
                model, features_array, feature_names
            )

            return {
                "recommended_kg": predicted,
                "confidence": confidence,
                "shap_explanation": shap_explanation,
                "model_version": artifact.version,
            }

        except Exception as exc:
            logger.warning("ML predict failed for cycle %s DOC %s: %s", cycle_id, doc, exc)
            return None

    @staticmethod
    def get_shap_explanation(model, features_array, feature_names: list) -> str:
        """Generate human-readable SHAP explanation for top 3 features."""
        if not _SHAP_AVAILABLE:
            return ""
        try:
            explainer = _shap_module.TreeExplainer(model)
            shap_values = explainer.shap_values(features_array)
            # shap_values shape: (1, n_features)
            sv = shap_values[0]
            top_indices = np.argsort(np.abs(sv))[::-1][:3]
            parts = []
            for idx in top_indices:
                name = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
                val = sv[idx]
                parts.append(f"{name} (shap={val:.2f})")
            total_shap = sum(sv[i] for i in top_indices)
            direction = "Increased" if total_shap >= 0 else "Reduced"
            pct = abs(total_shap) / (abs(float(features_array[0].mean())) + 1e-6) * 100
            pct = min(pct, 99.0)
            return f"{direction} {pct:.0f}%: {', '.join(parts)}"
        except Exception as exc:
            logger.warning("SHAP explanation failed: %s", exc)
            return ""

    @staticmethod
    def train_model() -> dict:
        """Train XGBoost on top-25% FCR completed cycles. Returns metrics dict."""
        if not _XGBOOST_AVAILABLE:
            return {"error": "xgboost not installed"}

        try:
            # Step 1: Load all inactive (completed) cycles with sufficient data
            completed_cycles = Cycle.objects(is_active=False)
            cycle_fcr_list = []

            for cycle in completed_cycles:
                cycle_id = str(cycle.id)
                cycle_data = CycleData.objects(cycle_id=cycle_id).first()
                if not cycle_data or not cycle_data.result_data:
                    continue
                data = cycle_data.result_data
                if len(data) < 20:
                    continue

                data_sorted = sorted(
                    [r for r in data if r.get("doc") is not None],
                    key=lambda x: x["doc"]
                )

                # Step 2: Compute final FCR
                total_feed = sum(r.get("feed_given_kg", 0) or 0 for r in data_sorted)
                if total_feed <= 0:
                    continue

                abw_rows = [(r["doc"], r["abw"]) for r in data_sorted if r.get("abw")]
                if not abw_rows:
                    continue
                last_abw = sorted(abw_rows, key=lambda x: x[0])[-1][1]

                first_row = data_sorted[0]
                initial_population = (
                    first_row.get("initial_stocking") or first_row.get("population")
                )
                if not initial_population:
                    for r in data_sorted:
                        if r.get("initial_stocking"):
                            initial_population = r["initial_stocking"]
                            break
                if not initial_population:
                    continue

                pop_rows = [(r["doc"], r["population"]) for r in data_sorted if r.get("population")]
                last_pop = sorted(pop_rows, key=lambda x: x[0])[-1][1] if pop_rows else None
                sr = (last_pop / initial_population) if last_pop else 0.8
                harvest_biomass = last_abw * sr * initial_population / 1000.0
                if harvest_biomass <= 0:
                    continue

                fcr = total_feed / harvest_biomass
                cycle_fcr_list.append((cycle_id, fcr))

            if len(cycle_fcr_list) < 4:
                return {"error": "insufficient completed cycles for training", "n_cycles": len(cycle_fcr_list)}

            # Step 3: Top 25% by FCR (lowest = most efficient)
            cycle_fcr_list.sort(key=lambda x: x[1])
            top_n = max(1, len(cycle_fcr_list) // 4)
            top_cycles = [cid for cid, _ in cycle_fcr_list[:top_n]]

            # Step 4: Extract features and labels for each DOC >= 30
            X_rows = []
            y_rows = []

            for cycle_id in top_cycles:
                cycle_data = CycleData.objects(cycle_id=cycle_id).first()
                if not cycle_data or not cycle_data.result_data:
                    continue
                data = cycle_data.result_data
                data_sorted = sorted(
                    [r for r in data if r.get("doc") is not None],
                    key=lambda x: x["doc"]
                )
                for row in data_sorted:
                    row_doc = row.get("doc")
                    if row_doc is None or row_doc < 30:
                        continue
                    label = row.get("feed_given_kg")
                    if label is None or label <= 0:
                        continue
                    feats = FeedingMLService.extract_features(cycle_id, row_doc)
                    if feats is None:
                        continue
                    X_rows.append([feats.get(f, 0.0) for f in FEATURE_NAMES])
                    y_rows.append(float(label))

            if len(X_rows) < 20:
                return {"error": "insufficient training samples", "n_samples": len(X_rows)}

            X = np.array(X_rows, dtype=float)
            y = np.array(y_rows, dtype=float)

            # Step 5: Train with 80/20 split (manual, no sklearn dependency)
            rng = np.random.default_rng(42)
            n = len(X)
            indices = rng.permutation(n)
            split = int(n * 0.8)
            train_idx, test_idx = indices[:split], indices[split:]
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                random_state=42,
                verbosity=0,
            )
            model.fit(X_train, y_train)

            # Step 6: Evaluate
            y_pred = model.predict(X_test)
            residuals = y_test - y_pred
            rmse = float(np.sqrt(np.mean(residuals ** 2)))
            mae = float(np.mean(np.abs(residuals)))
            ss_res = float(np.sum(residuals ** 2))
            ss_tot = float(np.sum((y_test - np.mean(y_test)) ** 2))
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

            metrics = {
                "rmse": rmse,
                "mae": mae,
                "r2": r2,
                "n_samples": len(X_rows),
                "n_cycles": len(top_cycles),
            }

            # Step 7: Minimum quality gate
            if r2 < 0.4:
                return {"skipped": True, "reason": "r2 below threshold", **metrics}

            # Step 8: Serialize and store
            model_bytes = pickle.dumps(model)
            version = datetime.utcnow().strftime("v%Y%m%d_%H%M%S")

            # Step 9: Deactivate previous active artifact
            FeedingModelArtifact.objects(is_active=True).update(set__is_active=False)

            artifact = FeedingModelArtifact(
                version=version,
                model_bytes=model_bytes,
                feature_names=FEATURE_NAMES,
                metrics=metrics,
                trained_at=datetime.utcnow(),
                is_active=True,
            )
            artifact.save()

            logger.info("Feeding ML model trained and saved: %s, metrics=%s", version, metrics)
            return metrics

        except Exception as exc:
            logger.exception("train_model failed: %s", exc)
            return {"error": str(exc)}
