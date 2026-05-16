"""
graph.py - System Graph (LangGraph State Machine)

Architecture:

    START
      │
      ▼
  ┌─────────────────┐
  │ input_guardrail  │  ← Programmatic message filter (no LLM)
  └────────┬────────┘
           │
     ┌─────┴─────┐
     │   Safe?   │
     └─────┬─────┘
       Yes │        No
           │         │
           ▼         ▼
  ┌────────────┐  ┌──────┐
  │  chatbot   │  │ END  │  ← Dangerous message blocked
  └─────┬──────┘  └──────┘
        │
  ┌─────┴─────┐
  │ tool_call? │
  └─────┬─────┘
    Yes │       No
        │        │
        ▼        ▼
  ┌──────────┐ ┌──────────────────┐
  │  tools   │ │ output_guardrail │
  └────┬─────┘ └────────┬─────────┘
       │                │
       ▼                ▼
  ┌──────────┐       ┌──────┐
  │ chatbot  │       │ END  │
  └──────────┘       └──────┘
"""
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import tools_condition

from agent.state import AgentState
from agent.nodes import input_guardrail, chatbot, tools_node, output_guardrail


# ============================================================
# Graph Construction
# ============================================================
graph_builder = StateGraph(AgentState)

# 1. Register nodes
graph_builder.add_node("input_guardrail", input_guardrail)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tools_node)
graph_builder.add_node("output_guardrail", output_guardrail)

# 2. Set entry point
graph_builder.set_entry_point("input_guardrail")

# 3. Conditional routing after input guardrail
def guardrail_router(state):
    if state.get("guardrail_passed", True):
        return "chatbot"
    else:
        return END

graph_builder.add_conditional_edges(
    "input_guardrail",
    guardrail_router,
    {"chatbot": "chatbot", END: END}
)

# 4. Conditional routing after chatbot
# If tool call requested → tools node
# If no tool call → output guardrail
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {"tools": "tools", END: "output_guardrail"}
)

# 5. After tools → back to chatbot
graph_builder.add_edge("tools", "chatbot")

# 6. After output guardrail → END
graph_builder.add_edge("output_guardrail", END)

# ============================================================
# Compile the graph
# ============================================================
agent_graph = graph_builder.compile()
