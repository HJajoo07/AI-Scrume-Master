from __future__ import annotations

import os

from models import AgentState


class ReportingAgent:
    def run(self, state: AgentState) -> AgentState:
        deterministic = self._deterministic_report(state)
        if os.getenv("LLM_PROVIDER", "").lower() == "openai" and os.getenv("OPENAI_API_KEY"):
            try:
                state.report = self._llm_report(state, deterministic)
                return state
            except Exception as exc:
                state.errors.append(f"LLM Reporting Agent fallback: {exc}")

        state.report = deterministic
        return state

    def _deterministic_report(self, state: AgentState) -> str:
        m = state.metrics
        risk_count = len(state.risks)
        lines = [
            f"## {state.sprint.name if state.sprint else 'Sprint'} Report",
            "",
            f"**Sprint health:** {m.forecast_status}",
            f"**Progress:** {m.done_issues}/{m.total_issues} issues done, {m.completed_points:.1f}/{m.planned_points:.1f} story points complete ({m.completion_pct:.1f}%).",
            f"**Blocked issues:** {m.blocked_issues}",
            f"**Risks identified:** {risk_count}",
            "",
            "### Key risks",
        ]
        if state.risks:
            for risk in state.risks[:6]:
                lines.append(f"- **{risk.severity}** `{risk.issue_key}` — {risk.reason} {risk.recommendation}")
        else:
            lines.append("- No material risks detected by the rules engine.")

        lines += ["", "### Capacity recommendations"]
        if state.capacity_recommendations:
            for rec in state.capacity_recommendations:
                lines.append(f"- {rec.recommendation}")
        else:
            lines.append("- No clear capacity imbalance detected from the configured team capacity.")

        lines += ["", "### Next actions"]
        actions = []
        if m.blocked_issues:
            actions.append("Resolve the blocked items and their dependencies first.")
        if state.capacity_recommendations:
            actions.append("Redistribute safe, non-blocked work away from overloaded members.")
        if m.forecast_status in {"AT_RISK", "HIGH_RISK"}:
            actions.append("Reconfirm the sprint goal and remove low-value scope if necessary.")
        if not actions:
            actions.append("Continue daily monitoring and verify that progress remains on track.")
        lines.extend([f"- {action}" for action in actions])
        return "\n".join(lines)

    def _llm_report(self, state: AgentState, deterministic: str) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPEN_BASE_URL"),
            )
        model = os.getenv("OPENAI_MODEL", "openai.gpt-4o")
        prompt = f"""You are an experienced Scrum Master. Turn the structured sprint analysis below into a concise management report. Do not invent facts. Separate facts from recommendations.\n\n{deterministic}"""
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You produce concise, evidence-based Scrum reports."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        
        return response.choices[0].message.content or deterministic
