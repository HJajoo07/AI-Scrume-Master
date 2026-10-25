from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Issue:
    key: str
    summary: str
    status: str
    assignee: str
    priority: str
    story_points: float
    sprint: str
    created_days_ago: int
    updated_days_ago: int
    blocked: bool = False
    dependency: Optional[str] = None
    original_estimate_hours: float = 0.0
    remaining_estimate_hours: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TeamMember:
    name: str
    capacity_hours: float


@dataclass
class Sprint:
    sprint_id: str
    name: str
    start_date: str
    end_date: str
    goal: str
    status: str


@dataclass
class SprintMetrics:
    total_issues: int = 0
    done_issues: int = 0
    in_progress_issues: int = 0
    todo_issues: int = 0
    blocked_issues: int = 0
    planned_points: float = 0.0
    completed_points: float = 0.0
    remaining_points: float = 0.0
    completion_pct: float = 0.0
    time_elapsed_pct: float = 0.0
    required_daily_points: float = 0.0
    current_daily_points: float = 0.0
    forecast_status: str = "UNKNOWN"


@dataclass
class Risk:
    severity: str
    issue_key: str
    reason: str
    recommendation: str


@dataclass
class CapacityRecommendation:
    overloaded_member: str
    spare_member: Optional[str]
    overloaded_hours: float
    spare_hours: float
    recommendation: str


@dataclass
class AgentState:
    sprint: Optional[Sprint] = None
    issues: List[Issue] = field(default_factory=list)
    team: List[TeamMember] = field(default_factory=list)
    metrics: SprintMetrics = field(default_factory=SprintMetrics)
    risks: List[Risk] = field(default_factory=list)
    capacity_recommendations: List[CapacityRecommendation] = field(default_factory=list)
    report: str = ""
    raw_jira_count: int = 0
    errors: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "sprint": asdict(self.sprint) if self.sprint else None,
            "issues": [i.to_dict() for i in self.issues],
            "team": [asdict(t) for t in self.team],
            "metrics": asdict(self.metrics),
            "risks": [asdict(r) for r in self.risks],
            "capacity_recommendations": [asdict(c) for c in self.capacity_recommendations],
            "report": self.report,
            "raw_jira_count": self.raw_jira_count,
            "errors": self.errors,
        }
