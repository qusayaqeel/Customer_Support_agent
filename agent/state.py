from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Represents the state of our customer support agent graph.
    """
    # The 'messages' list acts as our conversation memory.
    # The 'add_messages' reducer ensures new messages are appended rather than overwriting.
    messages: Annotated[Sequence[BaseMessage], add_messages]
