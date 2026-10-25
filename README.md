# AI Scrum Master Agent 🚀

A portfolio-ready, multi-agent Scrum analytics application that integrates with Jira to analyze sprint progress, identify delivery risks, evaluate team capacity, and generate a consolidated Scrum Master report.

Built using **Python, LangGraph, Jira REST API, and Streamlit**, the application automates key sprint analysis activities through a sequence of specialized agents.

## 📌 Features

- **Automated Sprint Analysis:** Retrieves and analyzes sprint issues and their statuses.
- **Sprint Progress Tracking:** Calculates completion metrics and provides burn-down-style insights.
- **Risk Detection:** Identifies potential blockers, stale issues, dependency risks, and schedule risks.
- **Team Capacity Analysis:** Compares estimated workload against available capacity and suggests workload redistribution.
- **Automated Reporting:** Combines analysis results into a consolidated Scrum Master report.
- **Interactive Dashboard:** Presents sprint metrics, risks, capacity insights, and reports through a Streamlit interface.
- **Multiple Data Sources:** Supports mock data for demonstration and Jira Cloud for live issue data.
- **Optional LLM Integration:** Can generate natural-language recommendations when an LLM provider is configured. The application can also produce a deterministic report without an LLM.

## 🏗️ Architecture

The application uses LangGraph to orchestrate five specialized agents. A shared state carries sprint data and analysis results through the workflow.

```text
                    Streamlit UI
                         |
                         v
                  LangGraph Workflow
                         |
                         v
                     Jira Agent
                         |
                         v
                    Sprint Agent
                         |
                         v
                     Risk Agent
                         |
                         v
                   Capacity Agent
                         |
                         v
                  Reporting Agent
                         |
                         v
                 Final Scrum Report
```

### Agent Responsibilities

| Agent | Responsibility |
|---|---|
| Jira Agent | Retrieves sprint issues from Jira or loads mock data. |
| Sprint Agent | Calculates sprint progress, completion metrics, and forecast insights. |
| Risk Agent | Identifies potential blockers, stale work, dependency risks, and schedule risks. |
| Capacity Agent | Evaluates workload against team capacity and recommends possible redistribution. |
| Reporting Agent | Consolidates agent outputs into a management-friendly Scrum report. |

### How It Works

1. The user launches the Streamlit application and starts the sprint analysis workflow.
2. The Jira Agent retrieves issue data from Jira or loads predefined demo data.
3. The Sprint Agent analyzes issue status and calculates sprint progress metrics.
4. The Risk Agent evaluates issues for potential delivery risks.
5. The Capacity Agent compares workload with available team capacity.
6. The Reporting Agent combines the findings into a consolidated report.
7. The Streamlit dashboard displays sprint insights and recommendations.

## 🛠️ Technology Stack

- **Language:** Python
- **Agent Orchestration:** LangGraph
- **User Interface:** Streamlit
- **Project Management Integration:** Jira Cloud REST API
- **Data Retrieval:** REST APIs and JQL
- **LLM Integration:** Optional OpenAI-compatible API
- **Configuration:** Environment variables using `.env`

## ⚙️ Operating Modes

### 1. Mock Mode

Run the application with predefined demonstration data. This mode is useful for exploring the dashboard without connecting to Jira.

Configure your `.env` file:

```env
DATA_SOURCE=mock
```

### 2. Jira Mode

Connect to Jira Cloud to retrieve real sprint issues using the Jira REST API and JQL.

Configure your `.env` file:

```env
DATA_SOURCE=jira

JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your_jira_api_token

JIRA_JQL=project = ABC AND sprint = "Sprint 20"
```

**Important configuration notes:**

- Replace the example Jira URL, email, token, project key, and sprint query with your own values.
- Configure the Jira story-point field according to your instance because custom field IDs can differ.
- Team capacity is optional and can be provided through `TEAM_CAPACITY_JSON` if supported by your project configuration.
- Never commit `.env`, API tokens, or other credentials to GitHub.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or a compatible version supported by your dependencies.
- Git.
- A Jira Cloud account and API token if using Jira mode.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-scrum-master-agent.git
cd ai-scrum-master-agent
```

Replace `YOUR_USERNAME` with your GitHub username and use your actual repository name.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On Windows Command Prompt:

```bat
.venv\Scripts\activate.bat
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file.

Windows Command Prompt:

```bat
copy .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS or Linux:

```bash
cp .env.example .env
```

Update `.env` with your required settings. Start with `DATA_SOURCE=mock` if you want to run the application without Jira credentials.

### 5. Run the Application

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal, usually [http://localhost:8501](http://localhost:8501).

## 🤖 Optional LLM Configuration

The application supports deterministic report generation without an LLM. To enable LLM-generated narrative recommendations, configure the provider and credentials supported by your implementation.

Example configuration for an OpenAI-compatible endpoint:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

If your implementation supports a custom OpenAI-compatible endpoint, configure its base URL using the environment variable expected by your code.

**Security:** Keep API keys in your local `.env` file. Do not publish credentials in source code, screenshots, logs, or GitHub commits.

## 📂 Project Structure

The exact structure may vary depending on your implementation.

```text
ai-scrum-master-agent/
├── agents/
│   ├── jira_agent.py
│   ├── sprint_agent.py
│   ├── risk_agent.py
│   ├── capacity_agent.py
│   └── reporting_agent.py
├── app.py
├── graph.py
├── models.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔐 Security and Configuration

Before pushing the project to GitHub, ensure that `.gitignore` includes sensitive and generated files where appropriate.

```gitignore
.env
.venv/
venv/
__pycache__/
*.py[cod]
.streamlit/secrets.toml
```

Commit `.env.example` with placeholder values, not real credentials.

## 🔮 Future Enhancements

- Store historical sprint metrics in PostgreSQL for trend analysis.
- Integrate Jira changelog history to estimate cycle time and velocity.
- Train and evaluate a sprint delivery-risk classifier using historical sprint data.
- Add Slack notifications for high-risk sprints.
- Schedule recurring sprint analysis using Apache Airflow.
- Add Jira write actions with explicit approval, permission checks, and audit logging.

## 🎯 Project Goal

The goal of the AI Scrum Master Agent is to reduce repetitive sprint reporting work, improve visibility into potential delivery risks, and help Scrum Masters and development teams make more informed sprint-planning decisions.

This project demonstrates practical use of multi-agent orchestration, REST API integration, workflow automation, and interactive analytics.

## 👨‍💻 Author

**Harshit Jajoo**

- GitHub: [Your GitHub Profile](https://github.com/YOUR_USERNAME)
- LinkedIn: [Your LinkedIn Profile](https://www.linkedin.com/in/YOUR_LINKEDIN_USERNAME/)
