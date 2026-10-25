from __future__ import annotations

from datetime import date

from models import AgentState, SprintMetrics


class SprintAgent:
    def run(self, state: AgentState) -> AgentState:
        metrics = SprintMetrics()
        metrics.total_issues = len(state.issues)
        metrics.done_issues = sum(i.status.lower() == "done" for i in state.issues)
        metrics.in_progress_issues = sum(i.status.lower() in {"in progress", "in development"} for i in state.issues)
        metrics.todo_issues = metrics.total_issues - metrics.done_issues - metrics.in_progress_issues
        metrics.blocked_issues = sum(i.blocked or i.status.lower() in {"blocked", "impediment"} for i in state.issues)

        metrics.planned_points = sum(i.story_points for i in state.issues)
        metrics.completed_points = sum(i.story_points for i in state.issues if i.status.lower() == "done")
        metrics.remaining_points = max(metrics.planned_points - metrics.completed_points, 0)
        metrics.completion_pct = (
            metrics.completed_points / metrics.planned_points * 100 if metrics.planned_points else 0
        )

        if state.sprint and state.sprint.start_date and state.sprint.end_date:
            try:
                start = date.fromisoformat(state.sprint.start_date)
                end = date.fromisoformat(state.sprint.end_date)
                total_days = max((end - start).days, 1)
                elapsed_days = max(min((date.today() - start).days, total_days), 0)
                metrics.time_elapsed_pct = elapsed_days / total_days * 100
                remaining_days = max(total_days - elapsed_days, 1)
                metrics.current_daily_points = metrics.completed_points / max(elapsed_days, 1)
                metrics.required_daily_points = metrics.remaining_points / remaining_days

                if metrics.current_daily_points >= metrics.required_daily_points:
                    metrics.forecast_status = "ON_TRACK"
                elif metrics.current_daily_points >= metrics.required_daily_points * 0.75:
                    metrics.forecast_status = "AT_RISK"
                else:
                    metrics.forecast_status = "HIGH_RISK"
            except ValueError:
                metrics.forecast_status = "UNKNOWN"
        else:
            metrics.forecast_status = "UNKNOWN"

        state.metrics = metrics
        return state
