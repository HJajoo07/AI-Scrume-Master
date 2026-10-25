from __future__ import annotations

import json
import os

from models import AgentState
from mock_data import get_mock_data
from services.jira_client import JiraClient


class JiraAgent:
    def run(self, state: AgentState) -> AgentState:
        data_source = os.getenv("DATA_SOURCE", "mock").lower()
        if data_source == "mock":
            sprint, issues, team = get_mock_data()
            state.sprint = sprint
            state.issues = issues
            state.team = team
            state.raw_jira_count = len(issues)
            return state

        required = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_JQL"]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            state.errors.append(f"Missing Jira configuration: {', '.join(missing)}")
            return state

        try:
            client = JiraClient(
                os.environ["JIRA_BASE_URL"],
                os.environ["JIRA_EMAIL"],
                os.environ["JIRA_API_TOKEN"],
                os.getenv("JIRA_STORY_POINTS_FIELD", "customfield_10016"),
            )
            issues = client.search_issues(os.environ["JIRA_JQL"])
            state.issues = issues
            state.raw_jira_count = len(issues)

            capacity_json = os.getenv("TEAM_CAPACITY_JSON", "")
            if capacity_json:
                try:
                    from models import TeamMember
                    state.team = [TeamMember(name, float(hours)) for name, hours in json.loads(capacity_json).items()]
                except (TypeError, ValueError, json.JSONDecodeError) as exc:
                    state.errors.append(f"Invalid TEAM_CAPACITY_JSON: {exc}")

            sprint_name = issues[0].sprint if issues and issues[0].sprint else "Configured Sprint"
            state.sprint = state.sprint or None
            if state.sprint is None:
                from models import Sprint
                state.sprint = Sprint(
                    sprint_id="jira",
                    name=sprint_name,
                    start_date="",
                    end_date="",
                    goal="",
                    status="ACTIVE",
                )
            #print(state)
            return state
        except Exception as exc:  # keep dashboard alive and expose the issue
            state.errors.append(f"Jira Agent error: {exc}")
            
            return state
