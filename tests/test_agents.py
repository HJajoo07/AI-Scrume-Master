import os

from agents.capacity_agent import CapacityAgent
from agents.risk_agent import RiskAgent
from agents.sprint_agent import SprintAgent
from models import AgentState
from mock_data import get_mock_data


def build_state():
    sprint, issues, team = get_mock_data()
    return AgentState(sprint=sprint, issues=issues, team=team)


def test_sprint_metrics():
    state = build_state()
    state = SprintAgent().run(state)
    assert state.metrics.total_issues == 10
    assert state.metrics.completed_points == 10
    assert state.metrics.planned_points == 43
    assert state.metrics.blocked_issues == 1


def test_risk_agent_finds_blockers_and_dependencies():
    state = build_state()
    state = SprintAgent().run(state)
    state = RiskAgent().run(state)
    keys = {risk.issue_key for risk in state.risks}
    assert "APP-102" in keys
    assert "APP-105" in keys
    assert "APP-109" in keys


def test_capacity_agent_finds_overload():
    state = build_state()
    state = CapacityAgent().run(state)
    assert state.capacity_recommendations
    assert state.capacity_recommendations[0].overloaded_member in {"Amit", "Raj"}
