from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from agents.capacity_agent import CapacityAgent
from agents.jira_agent import JiraAgent
from agents.reporting_agent import ReportingAgent
from agents.risk_agent import RiskAgent
from agents.sprint_agent import SprintAgent
from models import AgentState


class GraphState(TypedDict):
    state: AgentState


def _jira_node(data: GraphState) -> GraphState:
    return {"state": JiraAgent().run(data["state"])}


def _sprint_node(data: GraphState) -> GraphState:
    return {"state": SprintAgent().run(data["state"])}


def _risk_node(data: GraphState) -> GraphState:
    return {"state": RiskAgent().run(data["state"])}


def _capacity_node(data: GraphState) -> GraphState:
    return {"state": CapacityAgent().run(data["state"])}


def _report_node(data: GraphState) -> GraphState:
    return {"state": ReportingAgent().run(data["state"])}


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("jira_agent", _jira_node)
    graph.add_node("sprint_agent", _sprint_node)
    graph.add_node("risk_agent", _risk_node)
    graph.add_node("capacity_agent", _capacity_node)
    graph.add_node("reporting_agent", _report_node)

    graph.add_edge(START, "jira_agent")
    graph.add_edge("jira_agent", "sprint_agent")
    graph.add_edge("sprint_agent", "risk_agent")
    graph.add_edge("risk_agent", "capacity_agent")
    graph.add_edge("capacity_agent", "reporting_agent")
    graph.add_edge("reporting_agent", END)

    return graph.compile()
