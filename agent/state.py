from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Central system state - flows between all nodes in the Graph.
    
    Upgraded from a simple message memory to a full State Machine that tracks:
    - messages: Complete conversation history
    - funnel_stage: Current stage in the Sales Funnel
    - guardrail_passed: Whether the last message is safe and store-related
    """
    # Conversation history - Reducer ensures messages accumulate without overwriting
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Sales Funnel Stage:
    # greeting   = Initial welcome and exploration
    # discovery  = Gathering customer requirements (usage + budget)
    # pitching   = Presenting products from search results
    # closing    = Confirming purchase and collecting order details
    funnel_stage: str
    
    # Guardrail check result - whether the last message is safe or not
    guardrail_passed: bool
