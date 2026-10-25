from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List

import requests

from models import Issue, Sprint, TeamMember


class JiraClient:
    """Small Jira Cloud REST client using Basic auth (email + API token)."""

    def __init__(self, base_url: str, email: str, api_token: str, story_points_field: str = "customfield_10016"):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.story_points_field = story_points_field

    def _get(self, path: str, params: Dict | None = None) -> Dict:
        url = f"{self.base_url}{path}"
        response = requests.get(
            url,
            params=params,
            auth=(self.email, self.api_token),
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def search_issues(self, jql: str, max_results: int = 100) -> List[Issue]:
        # Jira Cloud currently exposes enhanced JQL search at POST /rest/api/3/search/jql.
        # POST avoids URL-length problems and matches Atlassian's current search API shape.
        fields = [
            "summary",
            "status",
            "assignee",
            "priority",
            "sprint",
            "created",
            "updated",
            self.story_points_field,
            "timeoriginalestimate",
            "timeestimate",
            "issuelinks",
        ]
        url = f"{self.base_url}/rest/api/3/search/jql"
        response = requests.post(
            url,
            json={
                "jql": jql,
                "maxResults": max_results,
                "fields": fields,
            },
            auth=(self.email, self.api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return [self._parse_issue(item) for item in data.get("issues", [])]

    def _parse_issue(self, item: Dict) -> Issue:
        fields = item.get("fields", {})
        assignee = fields.get("assignee") or {}
        priority = fields.get("priority") or {}
        status = fields.get("status") or {}
        sprint_value = fields.get("sprint") or {}
        story_points = fields.get(self.story_points_field) or 0
        summary = fields.get("summary") or item.get("key", "")

        # A simple heuristic for blocked items. You can later replace this with
        # a Jira field, label, or issue-link based rule.
        status_name = str(status.get("name", ""))
        blocked = status_name.lower() in {"blocked", "impediment"}

        def age_in_days(value):
            if not value:
                return 0
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                return max((datetime.now(timezone.utc) - dt).days, 0)
            except ValueError:
                return 0

        if isinstance(sprint_value, list):
            sprint_name = sprint_value[0].get("name") if sprint_value and isinstance(sprint_value[0], dict) else str(sprint_value[0]) if sprint_value else ""
        elif isinstance(sprint_value, dict):
            sprint_name = sprint_value.get("name", "")
        else:
            sprint_name = str(sprint_value)

        return Issue(
            key=item.get("key", "UNKNOWN"),
            summary=summary,
            status=status_name or "Unknown",
            assignee=assignee.get("displayName") or "Unassigned",
            priority=priority.get("name") or "Medium",
            story_points=float(story_points),
            sprint=sprint_name,
            created_days_ago=age_in_days(fields.get("created")),
            updated_days_ago=age_in_days(fields.get("updated")),
            blocked=blocked,
            original_estimate_hours=(fields.get("timeoriginalestimate") or 0) / 3600,
            remaining_estimate_hours=(fields.get("timeestimate") or 0) / 3600,
        )
