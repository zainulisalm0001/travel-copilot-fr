from pydantic import BaseModel, Field
from typing import List, Optional

class PlanRequest(BaseModel):
    origin: str = Field(..., example="CDG")
    cities: List[str] = Field(..., example=["Paris", "Lyon"])
    start_date: str
    end_date: str
    budget_eur: int = 1200
    party_size: int = 1
    pace: str = Field("medium", description="slow|medium|fast")
    interests: List[str] = Field(default_factory=lambda: ["food", "art", "history"])
    max_walk_km_per_day: float = 10.0
    language: str = Field("en", description="en|fr")

class Activity(BaseModel):
    title: str
    city: str
    start_time: str
    end_time: str
    cost_eur: float
    transport_mode: str
    url: Optional[str] = None

class DayPlan(BaseModel):
    date: str
    city: str
    activities: List[Activity]

class PlanResponse(BaseModel):
    summary: str
    total_cost_estimate_eur: float
    days: List[DayPlan]
    citations: List[str] = []