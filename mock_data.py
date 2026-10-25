from models import Issue, Sprint, TeamMember


def get_mock_data():
    sprint = Sprint(
        sprint_id="20",
        name="Sprint 20",
        start_date="2026-10-01",
        end_date="2026-10-14",
        goal="Complete authentication, payment integration, and dashboard MVP.",
        status="ACTIVE",
    )

    team = [
        TeamMember("Rahul", 40),
        TeamMember("Amit", 30),
        TeamMember("Neha", 40),
        TeamMember("Raj", 20),
    ]

    issues = [
        Issue("APP-101", "Login API", "Done", "Rahul", "High", 5, "Sprint 20", 18, 1, original_estimate_hours=12, remaining_estimate_hours=0),
        Issue("APP-102", "Payment gateway", "Blocked", "Amit", "Highest", 8, "Sprint 20", 12, 5, blocked=True, original_estimate_hours=30, remaining_estimate_hours=22),
        Issue("APP-103", "Dashboard UI", "In Progress", "Neha", "High", 5, "Sprint 20", 10, 1, original_estimate_hours=22, remaining_estimate_hours=10),
        Issue("APP-104", "JWT refresh", "Done", "Rahul", "Medium", 3, "Sprint 20", 16, 2, original_estimate_hours=8, remaining_estimate_hours=0),
        Issue("APP-105", "Database migration", "In Progress", "Raj", "High", 5, "Sprint 20", 8, 4, dependency="APP-102", original_estimate_hours=18, remaining_estimate_hours=12),
        Issue("APP-106", "Audit logging", "To Do", "Amit", "Medium", 3, "Sprint 20", 7, 7, original_estimate_hours=12, remaining_estimate_hours=12),
        Issue("APP-107", "Unit tests", "Done", "Neha", "Medium", 2, "Sprint 20", 13, 1, original_estimate_hours=8, remaining_estimate_hours=0),
        Issue("APP-108", "Admin permissions", "In Progress", "Amit", "High", 5, "Sprint 20", 9, 6, original_estimate_hours=20, remaining_estimate_hours=15),
        Issue("APP-109", "Payment callback", "To Do", "Raj", "Highest", 5, "Sprint 20", 6, 6, dependency="APP-102", original_estimate_hours=18, remaining_estimate_hours=18),
        Issue("APP-110", "Dashboard tests", "In Progress", "Neha", "Medium", 2, "Sprint 20", 6, 3, original_estimate_hours=10, remaining_estimate_hours=5),
    ]
    return sprint, issues, team
