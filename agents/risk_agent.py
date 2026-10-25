from __future__ import annotations

from models import AgentState, Risk


class RiskAgent:
    def run(self, state: AgentState) -> AgentState:
        risks = []
        for issue in state.issues:
            if issue.blocked or issue.status.lower() in {"blocked", "impediment"}:
                risks.append(
                    Risk("HIGH", issue.key, "Issue is blocked.", "Resolve the blocker before starting dependent work.")
                )
            elif issue.priority.lower() in {"highest", "critical"} and issue.status.lower() == "to do":
                risks.append(
                    Risk("HIGH", issue.key, "Critical work has not started.", "Start or re-plan the highest-priority item immediately.")
                )
            elif issue.updated_days_ago >= 5 and issue.status.lower() != "done":
                risks.append(
                    Risk("MEDIUM", issue.key, f"No update for {issue.updated_days_ago} days.", "Ask the assignee for a status update and identify impediments.")
                )
            if issue.dependency:
                risks.append(
                    Risk("HIGH", issue.key, f"Depends on {issue.dependency}.", "Resolve the dependency or split work to avoid waiting.")
                )

        if state.metrics.forecast_status == "HIGH_RISK":
            risks.append(
                Risk("HIGH", "SPRINT", "Current delivery pace is materially below the required pace.", "Reduce scope, unblock work, or redistribute capacity.")
            )
        elif state.metrics.forecast_status == "AT_RISK":
            risks.append(
                Risk("MEDIUM", "SPRINT", "Current delivery pace may miss the sprint goal.", "Prioritize remaining high-value work and monitor daily.")
            )

        state.risks = risks
        return state
