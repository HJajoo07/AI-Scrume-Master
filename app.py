from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from rag_chatbot import RAGChatbot
from graph import build_graph
from models import AgentState


# ==================================================
# CONFIGURATION
# ==================================================

load_dotenv()

st.set_page_config(
    page_title="AI Scrum Master Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("AI Scrum Master Agent")
st.caption(
    "Jira → Sprint analysis → Risk detection → Capacity analysis → AI report"
)


# ==================================================
# SIDEBAR CONFIGURATION + DASHBOARD BUTTON
# ==================================================

with st.sidebar:
    st.header("Configuration")

    mode = st.radio(
        "Data source",
        ["Mock demo", "Jira Cloud"],
        index=(
            0
            if os.getenv("DATA_SOURCE", "mock").lower() == "mock"
            else 1
        ),
    )

    if mode == "Jira Cloud":
        st.info("Set Jira credentials and JQL in your .env file.")
        st.code(
            'JIRA_BASE_URL=...\n'
            'JIRA_EMAIL=...\n'
            'JIRA_API_TOKEN=...\n'
            'JIRA_JQL=project = ABC AND sprint = "Sprint 20"'
        )

    use_llm = st.toggle(
        "Use optional LLM report",
        value=bool(os.getenv("OPENAI_API_KEY")),
    )

    # Apply the sidebar settings before the graph is executed.
    os.environ["DATA_SOURCE"] = "mock" if mode == "Mock demo" else "jira"
    os.environ["LLM_PROVIDER"] = "openai" if use_llm else ""

    st.divider()
    if st.button("📊 Analyze Sprint", type="primary", width="stretch"):
        # The graph runs automatically on startup. This button only switches
        # from the Copilot home page to the dashboard.
        st.session_state["show_dashboard"] = True


# ==================================================
# AUTOMATIC SPRINT ANALYSIS
# Run once on startup, and again if sidebar configuration changes.
# ==================================================

current_config = (mode, use_llm)
last_attempted_config = st.session_state.get("analysis_attempt_config")

should_run_analysis = last_attempted_config != current_config

if should_run_analysis:
    # Avoid accidentally showing stale data when configuration changes.
    st.session_state.pop("analysis", None)
    st.session_state.pop("analysis_error", None)
    st.session_state["analysis_attempt_config"] = current_config
    st.session_state["analysis_config"] = current_config
    st.session_state["rag_chat_history"] = []

    try:
        with st.spinner("Analyzing sprint automatically..."):
            result = build_graph().invoke({"state": AgentState()})
            st.session_state["analysis"] = result["state"]
    except Exception as exc:
        st.session_state["analysis_error"] = (
            f"Sprint analysis failed: {type(exc).__name__}: {exc}"
        )

state = st.session_state.get("analysis")
analysis_error = st.session_state.get("analysis_error")


# ==================================================
# CHATBOT RENDERER
# ==================================================

def render_chatbot(analysis_state: AgentState | None) -> None:
    """Display the Copilot chat and keep history across Streamlit reruns."""
    st.subheader("💬 Ask Your Sprint Copilot")
    st.caption(
        "Ask questions about sprint progress, Jira issues, risks, "
        "team capacity, and recommendations. Answers use the latest analysis."
    )

    if analysis_error:
        st.warning(
            "The sprint analysis is not available, so the chatbot cannot "
            "answer from current sprint data. Check the error above and "
            "correct the configuration before restarting the app."
        )
        return

    if analysis_state is None:
        st.info("Sprint analysis is not available yet.")
        return

    if "rag_chat_history" not in st.session_state:
        st.session_state["rag_chat_history"] = []

    history_col, clear_col = st.columns([5, 1])
    with clear_col:
        if st.button("Clear chat", key="clear_rag_chat"):
            st.session_state["rag_chat_history"] = []
            st.rerun()

    for message in st.session_state["rag_chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask about sprint progress, issues, risks, or capacity..."
    )

    if question:
        previous_history = list(st.session_state["rag_chat_history"])

        st.session_state["rag_chat_history"].append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching sprint data..."):
                try:
                    chatbot = RAGChatbot(top_k=5)
                    answer = chatbot.answer(
                        state=analysis_state,
                        question=question,
                        history=previous_history,
                    )
                except Exception as exc:
                    answer = (
                        "The chatbot encountered an unexpected error. "
                        f"Error type: {type(exc).__name__}."
                    )

            st.markdown(answer)

        st.session_state["rag_chat_history"].append(
            {"role": "assistant", "content": answer}
        )


# ==================================================
# HOME PAGE: COPILOT FIRST
# ==================================================

if not st.session_state.get("show_dashboard", False):
    if analysis_error:
        st.error(analysis_error)
    elif state is not None:
        st.success("Sprint analysis is ready. Open Analyze Sprint in the sidebar to view the dashboard.")

    render_chatbot(state)
    st.stop()


# ==================================================
# DASHBOARD: VISIBLE AFTER CLICKING ANALYZE SPRINT
# ==================================================

if analysis_error:
    st.error(analysis_error)
    st.info("Fix the configuration and restart the app to retry the analysis.")
    render_chatbot(state)
    st.stop()

if state is None:
    st.error("No sprint analysis is available.")
    render_chatbot(state)
    st.stop()

if state.errors:
    st.subheader("Analysis Warnings")
    for error in state.errors:
        st.warning(error)

m = state.metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Issues", m.total_issues)
c2.metric("Completed", f"{m.completed_points:.0f} pts")
c3.metric("Progress", f"{m.completion_pct:.1f}%")
c4.metric("Health", m.forecast_status)

st.subheader(state.sprint.name if state.sprint else "Sprint")
st.write(
    state.sprint.goal
    if state.sprint and state.sprint.goal
    else "Sprint loaded from the configured data source."
)

left, right = st.columns(2)

with left:
    st.subheader("Sprint Details")
    sprint_rows = [
        ["Total issues", m.total_issues],
        ["Done", m.done_issues],
        ["In progress", m.in_progress_issues],
        ["To do", m.todo_issues],
        ["Blocked", m.blocked_issues],
        ["Planned points", m.planned_points],
        ["Completed points", m.completed_points],
        ["Remaining points", m.remaining_points],
    ]
    st.dataframe(
        pd.DataFrame(sprint_rows, columns=["Metric", "Value"]),
        hide_index=True,
        width="stretch",
    )

with right:
    st.subheader("Issue Board")
    issue_df = pd.DataFrame([issue.to_dict() for issue in state.issues])
    if not issue_df.empty:
        desired_columns = [
            "key", "summary", "status", "assignee", "priority",
            "story_points", "blocked",
        ]
        available_columns = [
            column for column in desired_columns if column in issue_df.columns
        ]
        st.dataframe(
            issue_df[available_columns],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No issues found in the current analysis.")

st.subheader("⚠️ Risks")
if state.risks:
    risk_df = pd.DataFrame([risk.__dict__ for risk in state.risks])
    st.dataframe(risk_df, hide_index=True, width="stretch")
else:
    st.success("No material risks detected.")

st.subheader("👥 Capacity")
if state.capacity_recommendations:
    capacity_df = pd.DataFrame(
        [recommendation.__dict__ for recommendation in state.capacity_recommendations]
    )
    st.dataframe(capacity_df, hide_index=True, width="stretch")
else:
    st.success("No clear capacity imbalance detected.")

st.subheader("📋 Scrum Master Report")
if state.report:
    st.markdown(state.report)
else:
    st.info("No report is available for this analysis.")

# The Copilot appears below the dashboard once Analyze Sprint is clicked.
st.divider()
render_chatbot(state)
