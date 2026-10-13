from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Role(StrEnum):
    scout = "Knowledge Scout"
    scientist = "Research Scientist"
    engineer = "Research Engineer"
    critic = "Critic"
    replicator = "Replication Scientist"
    statistician = "Statistician"
    builder = "Tool Builder"
    innovator = "Innovation Scout"
    librarian = "Librarian"
    director = "Research Director"
    security = "Security Agent"
    professor = "Professor"
    student = "Student"
    cafe_worker = "Café Worker"
    shopkeeper = "Shopkeeper"
    journalist = "Journalist"
    entrepreneur = "Entrepreneur"
    doctor = "Doctor"
    police = "Police Officer"
    citizen = "Citizen"


class Personality(Schema):
    creativity: float = Field(.65, ge=0, le=1)
    skepticism: float = Field(.7, ge=0, le=1)
    risk_tolerance: float = Field(.2, ge=0, le=1)
    curiosity: float = Field(.8, ge=0, le=1)
    persistence: float = Field(.8, ge=0, le=1)
    collaboration: float = Field(.7, ge=0, le=1)
    novelty_preference: float = Field(.6, ge=0, le=1)
    evidence_threshold: float = Field(.95, ge=0, le=1)


class Belief(Schema):
    claim: str = Field(max_length=2000)
    belief_type: Literal["observation", "claim", "belief", "hypothesis", "rumor", "inference"] = "claim"
    confidence: float = Field(.5, ge=0, le=1)
    sources: list[str] = Field(default_factory=list, max_length=20)
    contradictions: list[str] = Field(default_factory=list, max_length=20)
    last_verified: str | None = None


class Agent(Schema):
    id: str = Field(default_factory=lambda: uid("agent"))
    name: str
    role: Role
    created_at: str = Field(default_factory=now)
    state: str = "idle"
    specialization: list[str] = Field(default_factory=lambda: ["information retrieval"])
    personality: Personality = Field(default_factory=Personality)
    beliefs: list[Belief] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    plan: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    relationships: dict[str, float] = Field(default_factory=dict)
    reputation: dict[str, float] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)
    research_history: list[str] = Field(default_factory=list)
    schedule: dict[str, Any] = Field(default_factory=lambda: {"lod": 0, "wake_reason": None})


class MemoryWrite(Schema):
    kind: Literal["working", "episodic", "semantic", "procedural", "research", "social", "failure", "skill"] = "episodic"
    content: str = Field(min_length=1, max_length=3000)
    importance: float = Field(.5, ge=0, le=1)
    confidence: float = Field(.5, ge=0, le=1)
    sources: list[str] = Field(default_factory=list, max_length=20)


class Action(Schema):
    action: Literal["message", "research.search", "knowledge.query", "reflect"]
    recipient: str | None = None
    content: str = Field(default="", max_length=3000)


class Cognition(Schema):
    thought_summary: str = Field(max_length=4000)
    current_goal: str = Field(max_length=2000)
    belief_updates: list[Belief] = Field(default_factory=list, max_length=8)
    proposed_actions: list[Action] = Field(default_factory=list, max_length=3)
    memory_write: list[MemoryWrite] = Field(default_factory=list, max_length=5)
    confidence: float = Field(ge=0, le=1)


class HypothesisDraft(Schema):
    title: str = Field(min_length=5, max_length=200)
    mechanism: str = Field(min_length=10, max_length=2500)
    prediction: str = Field(min_length=10, max_length=1500)
    required_experiment: str = Field(max_length=2000)
    expected_metric_change: dict[str, float] = Field(default_factory=dict)
    plausibility: float = Field(ge=0, le=1)


class Review(Schema):
    approved: bool
    criticisms: list[str] = Field(min_length=1, max_length=10)
    controls: list[str] = Field(min_length=1, max_length=10)


class CodeDraft(Schema):
    explanation: str = Field(max_length=2500)
    code: str = Field(min_length=20, max_length=14000)


class ProjectCreate(Schema):
    title: str = Field(min_length=3, max_length=160)
    question: str = Field(min_length=10, max_length=3000)
    experiment_budget: int = Field(default=3, ge=1, le=20)
    token_budget: int = Field(default=48000, ge=4096, le=200000)
    time_budget_seconds: int = Field(default=1800, ge=60, le=86400)


class MessageCreate(Schema):
    recipient: str
    content: str = Field(min_length=1, max_length=3000)
    kind: Literal["message", "question", "request", "proposal", "critique", "paper", "experiment_result", "review", "task_assignment", "warning"] = "message"
