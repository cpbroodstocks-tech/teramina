# pylint: disable=W0102
import pandas as pd
import numpy as np

from teramina.water_quality_dashboard.models.variable_model import Variable

COLUMN_MAPPER = {
    "PL": "seed_cost",
    "feed": "feeding_cost",
    "chem/prob": "probiotic_cost",
    "other": "other_cost",
    "listrik": "energy_cost",
    "panen": "harvest_cost",
    "bonus": "bonus_cost",
    "gaji": "labor_cost",
}


def cost_data_preprocessing(
    cost_item: pd.DataFrame,
    cost_spending: pd.DataFrame,
    column_mapper: dict = COLUMN_MAPPER,
) -> pd.DataFrame:
    """cost data preprocessing

    Args:
      cost_item (pd.DataFrame): dataframe of cost item data
      cost_spending (pd.DataFrame): datafrom of daily cost spending
      column_mapper (dict): column mapper data
    Returns:
      (pd.dataFrame): dataframe of prepared cost data
    """

    kategori = cost_item["kategori"].unique()
    items = {}
    for i in kategori:
        items[i] = cost_item[cost_item["kategori"] == i]["bahan"].tolist()

    cost = {}
    for i, j in items.items():
        cost_spending_data = []
        for x in j:
            unit_cost = cost_item[cost_item["bahan"] == x]["harga_satuan"].values[0]
            cost_spending_data.append(cost_spending[x].values * unit_cost)

        cost_spending_data = np.array(cost_spending_data)
        cost_spending_data = np.nan_to_num(cost_spending_data)

        cost[i] = np.sum(cost_spending_data, axis=0)

    cost_df = pd.DataFrame(cost)
    cost_df.rename(columns=column_mapper, inplace=True)
    return cost_df


def sr_data_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    """sr data preprocessing

    Normalizes SR to [0,1], interpolates gaps, and enforces monotone non-increasing
    via cummin. SR given as percentage (e.g. 95) is normalized to fraction (0.95).
    Values that remain > 1 after normalization are clipped to 1.

    Args:
        df (pd.DataFrame): main dataframe

    Returns
        (pd.DataFrame): prepared dataframe
    """
    sr = pd.to_numeric(df["sr"], errors="coerce")
    # normalize percentage values (e.g. 95 → 0.95)
    sr = sr.where(sr <= 1, sr / 100)
    # clip to valid fraction range
    sr = sr.clip(0.0, 1.0)
    # fill gaps: linear interpolation between known values, backfill for leading NaN
    sr = sr.interpolate(method="linear").bfill()
    # if still NaN (entire column missing), default to 1.0
    sr = sr.fillna(1.0)
    # enforce monotone non-increasing (SR only ever decreases over cycle)
    sr = sr.cummin()
    df["sr"] = sr
    return df


def detect_gap_windows(df: pd.DataFrame, cols: list, max_gap: int = 3) -> dict:
    """Return contiguous NaN runs longer than max_gap for each column.

    Args:
        df: dataframe with a 'doc' column
        cols: columns to inspect
        max_gap: runs <= this length are considered normal; only longer runs are flagged

    Returns:
        dict mapping column name → list of {"start_doc": int, "end_doc": int, "length": int}
    """
    gaps = {}
    for col in cols:
        if col not in df.columns:
            continue
        is_null = df[col].isna()
        if not is_null.any():
            continue
        col_gaps = []
        run_start = None
        for idx, null in enumerate(is_null):
            if null and run_start is None:
                run_start = idx
            elif not null and run_start is not None:
                run_len = idx - run_start
                if run_len > max_gap:
                    start_doc = int(df["doc"].iat[run_start]) if "doc" in df.columns else run_start
                    end_doc = int(df["doc"].iat[idx - 1]) if "doc" in df.columns else idx - 1
                    col_gaps.append({"start_doc": start_doc, "end_doc": end_doc, "length": run_len})
                run_start = None
        # handle trailing run
        if run_start is not None:
            run_len = len(is_null) - run_start
            if run_len > max_gap:
                start_doc = int(df["doc"].iat[run_start]) if "doc" in df.columns else run_start
                end_doc = int(df["doc"].iat[-1]) if "doc" in df.columns else len(is_null) - 1
                col_gaps.append({"start_doc": start_doc, "end_doc": end_doc, "length": run_len})
        if col_gaps:
            gaps[col] = col_gaps
    return gaps


def smart_impute(df: pd.DataFrame) -> pd.DataFrame:
    """Apply field-specific imputation strategies for sensor columns.

    Strategies:
    - DO, temperature, NH3: forward-fill (carry last known reading), then backfill for
      leading NaN (sensor not yet connected at cycle start)
    - initial_stocking: backfill first valid value (stocking count known from day 1),
      then forward-fill trailing NaN
    - ABW: linear interpolation between weigh-in events, edge-fill with nearest value
    - SR: excluded here — handled by sr_data_preprocessing (cummin monotone logic)

    Args:
        df: dataframe after doc-gap completion

    Returns:
        df with NaN filled using per-column strategy
    """
    ffill_cols = ["do", "temperature", "nh3"]
    for col in ffill_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()

    if "initial_stocking" in df.columns:
        df["initial_stocking"] = df["initial_stocking"].bfill().ffill()

    if "abw" in df.columns:
        df["abw"] = df["abw"].interpolate(method="linear").ffill().bfill()

    return df


def waterquality_columns_checker(columns) -> list:
    """water quality checker"""
    var = Variable.objects().first()
    variables = list(var.data)
    variables = [i for i in variables if i not in ["temperature", "do", "nh3"]]
    added_columns = [i for i in columns if i in variables]
    return added_columns
