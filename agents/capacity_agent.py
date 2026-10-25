from __future__ import annotations

from collections import defaultdict

from models import AgentState, CapacityRecommendation


class CapacityAgent:
    def run(self, state: AgentState) -> AgentState:
        workload = defaultdict(float)
        for issue in state.issues:
            if issue.status.lower() != "done":
                workload[issue.assignee] += max(issue.remaining_estimate_hours, issue.original_estimate_hours, 0)

        capacity = {member.name: member.capacity_hours for member in state.team}
        recommendations = []

        overloaded = []
        spare = []
        for name, hours in workload.items():
            cap = capacity.get(name, 0)
            if cap <= 0:
                continue
            delta = hours - cap
            if delta > 4:
                overloaded.append((name, delta, hours, cap))
            elif cap - hours >= 8:
                spare.append((name, cap - hours, hours, cap))

        overloaded.sort(key=lambda x: x[1], reverse=True)
        spare.sort(key=lambda x: x[1], reverse=True)

        for name, excess, hours, cap in overloaded:
            target = spare[0] if spare else None
            spare_name = target[0] if target else None
            spare_hours = target[1] if target else 0
            recommendation = (
                f"Move roughly {min(excess, spare_hours):.1f} hours of non-blocked work from {name} to {spare_name}."
                if target
                else f"{name} is over capacity by about {excess:.1f} hours; reduce scope or add support."
            )
            recommendations.append(
                CapacityRecommendation(name, spare_name, round(excess, 1), round(spare_hours, 1), recommendation)
            )

        state.capacity_recommendations = recommendations
        return state
