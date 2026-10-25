from graph import build_graph
from models import AgentState

result = build_graph().invoke({"state": AgentState()})
print(result["state"].report)
