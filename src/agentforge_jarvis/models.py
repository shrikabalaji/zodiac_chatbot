from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Domain = Literal["analytics", "marketing", "hr", "operations", "finance", "general-management"]
Challenge = Literal["baseline", "budget-cut", "supply-delay", "sentiment-shift", "demand-surge"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Candidate(StrictModel):
    candidate_id: str = Field(min_length=1, max_length=40)
    skills: list[str] = Field(max_length=20)
    work_sample_score: float = Field(ge=0, le=100)


class Signal(StrictModel):
    channel: str = Field(min_length=1, max_length=60)
    responses: int = Field(gt=0, le=1000000)
    positive: int = Field(ge=0, le=1000000)
    previous_positive_rate: float = Field(ge=0, le=1)


class Scenario(StrictModel):
    name: str = Field(default="Project Monsoon", min_length=1, max_length=100)
    company: str = Field(default="Aster Foods · fictional", min_length=1, max_length=100)
    brief: str = Field(
        default="Launch a shelf-stable millet snack in Chennai and Bengaluru within 12 weeks, protecting customer trust and cash runway.",
        min_length=10,
        max_length=6000,
    )
    budget: float = Field(default=2400000, gt=0, le=1e10)
    units: int = Field(default=30000, gt=0, le=10000000)
    price: float = Field(default=120, gt=0, le=1e6)
    unit_cost: float = Field(default=65, ge=0, le=1e6)
    fixed_cost: float = Field(default=250000, ge=0, le=1e10)
    marketing_budget: float = Field(default=180000, ge=0, le=1e10)
    margin_target: float = Field(default=38, ge=0, le=100)
    launch_days: int = Field(default=84, gt=0, le=730)
    lead_days: int = Field(default=21, ge=0, le=730)
    production_per_day: int = Field(default=600, gt=0, le=10000000)
    team_fte: float = Field(default=8, ge=0, le=10000)
    required_fte: float = Field(default=10, gt=0, le=10000)
    hire_cost: float = Field(default=10000, ge=0, le=10000000)
    required_skills: list[str] = Field(
        default_factory=lambda: ["planning", "communication"], max_length=20
    )
    candidates: list[Candidate] = Field(
        default_factory=lambda: [
            Candidate(
                candidate_id="C-101",
                skills=["planning", "communication", "logistics"],
                work_sample_score=82,
            ),
            Candidate(
                candidate_id="C-102", skills=["planning", "data analysis"], work_sample_score=91
            ),
            Candidate(
                candidate_id="C-103", skills=["communication", "sales"], work_sample_score=77
            ),
        ],
        max_length=100,
    )
    signals: list[Signal] = Field(
        default_factory=lambda: [
            Signal(
                channel="Retail trials", responses=120, positive=92, previous_positive_rate=0.70
            ),
            Signal(
                channel="Creator sampling", responses=90, positive=71, previous_positive_rate=0.72
            ),
            Signal(
                channel="Campus survey", responses=150, positive=98, previous_positive_rate=0.68
            ),
        ],
        min_length=1,
        max_length=30,
    )
    labelling_concern: bool = False
    evidence_note: str = Field(
        default="Fictional teaching inputs; unit economics, channels and candidates extend the original workshop scenario. Not market forecasts.",
        max_length=1000,
    )


class AgentReport(StrictModel):
    domain: Domain
    headline: str
    recommendation: str
    metrics: dict[str, float | int | str | bool]
    evidence: list[str]
    assumptions: list[str]
    risks: list[str]
    actions: list[dict[str, str]]
    details: list[dict] = Field(default_factory=list)
    status: Literal["ready", "review", "hold"] = "review"
    narrative: str = ""
    tools_called: list[str] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)


class RunRequest(StrictModel):
    team: str = Field(default="liba-team-01", pattern=r"^[a-zA-Z0-9_-]{1,48}$")
    challenge: Challenge = "baseline"
    scenario: Scenario = Field(default_factory=Scenario)
    domain: Domain | None = None


class ChatRequest(RunRequest):
    message: str = Field(min_length=1, max_length=6000)


class NoteRequest(StrictModel):
    team: str = Field(default="liba-team-01", pattern=r"^[a-zA-Z0-9_-]{1,48}$")
    title: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=30000)


class BlueprintRequest(StrictModel):
    team: str = Field(default="liba-team-01", pattern=r"^[a-zA-Z0-9_-]{1,48}$")
    instructions: str = Field(max_length=4000)


def apply_challenge(scenario: Scenario, challenge: Challenge) -> Scenario:
    s = scenario.model_copy(deep=True)
    if any(x.positive > x.responses for x in s.signals):
        raise ValueError("Positive responses cannot exceed total responses.")
    if len({c.candidate_id for c in s.candidates}) != len(s.candidates):
        raise ValueError("Candidate IDs must be unique.")
    if challenge == "budget-cut":
        s.budget *= 0.75
    elif challenge == "supply-delay":
        s.lead_days += 14
    elif challenge == "sentiment-shift":
        s.labelling_concern = True
        for signal in s.signals:
            signal.positive = int(signal.positive * 0.7)
    elif challenge == "demand-surge":
        s.units = round(s.units * 1.4)
    return s
