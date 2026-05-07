# pylint: disable=missing-class-docstring

from typing import List, Optional
from pydantic import BaseModel


class HarvestScenarioParamsSchema(BaseModel):
    """Parameters for a single simulation run."""
    type: str              # "date_range" | "partial" | "price_sensitivity"
    doc_start: Optional[int] = None
    doc_end: Optional[int] = None
    step_days: Optional[int] = 7
    partial_pct: Optional[float] = None     # 0–100
    doc_partial: Optional[int] = None
    doc_final: Optional[int] = None
    sr_decay_pct_per_week: Optional[float] = None   # for risk scenarios


class RunSimulationSchema(BaseModel):
    price_per_kg: Optional[int] = None    # override shrimp price (IDR)
    scenarios: List[HarvestScenarioParamsSchema]


class SaveScenarioSchema(BaseModel):
    name: str
    params: dict
    results: list
