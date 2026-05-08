"""
graph.py - مخطط النظام (System Graph) v2

المعمارية:

    START
      │
      ▼
  ┌─────────────────┐
  │ input_guardrail  │  ← حارس المدخلات: يفحص الرسالة برمجياً
  └────────┬────────┘
           │
     ┌─────┴─────┐
     │  آمنة؟    │
     └─────┬─────┘
       نعم │        لا
           │         │
           ▼         ▼
  ┌────────────┐  ┌──────┐
  │  chatbot   │  │ END  │  ← الرسالة الخطيرة تُحظر
  └─────┬──────┘  └──────┘
        │
  ┌─────┴─────┐
  │ tool_call? │
  └─────┬─────┘
    نعم │       لا
        │        │
        ▼        ▼
  ┌──────────┐ ┌──────────────────┐
  │  tools   │ │ output_guardrail │  ← حارس المخرجات: يفحص رد الموديل
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
# بناء المخطط (Graph Construction)
# ============================================================
graph_builder = StateGraph(AgentState)

# 1. تسجيل العُقد (4 عُقد)
graph_builder.add_node("input_guardrail", input_guardrail)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tools_node)
graph_builder.add_node("output_guardrail", output_guardrail)

# 2. نقطة البداية
graph_builder.set_entry_point("input_guardrail")

# 3. التوجيه بعد حارس المدخلات
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

# 4. التوجيه بعد الموديل
# إذا طلب أداة → tools
# إذا لم يطلب → output_guardrail (فحص الرد قبل الإرسال)
def chatbot_router(state):
    """بديل لـ tools_condition يوجه للـ output_guardrail بدل END"""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    else:
        return "output_guardrail"

graph_builder.add_conditional_edges(
    "chatbot",
    chatbot_router,
    {"tools": "tools", "output_guardrail": "output_guardrail"}
)

# 5. بعد الأدوات → يعود للموديل
graph_builder.add_edge("tools", "chatbot")

# 6. بعد حارس المخرجات → ينتهي
graph_builder.add_edge("output_guardrail", END)

# ============================================================
# تجميع المخطط
# ============================================================
agent_graph = graph_builder.compile()
