import time
import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Any
from langchain_core.messages import HumanMessage
from agent.graph import agent_graph

router = APIRouter(prefix="/api")

# In-memory session storage
user_sessions = {}
SESSION_TIMEOUT = 30 * 60  # 30 minutes
MAX_MESSAGES = 20

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    products: Optional[List[Any]] = None
    funnel_stage: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    current_time = time.time()
    session_id = req.session_id
    user_text = req.message
    
    # Reset session on /start
    if user_text.strip() == "/start":
        if session_id in user_sessions:
            del user_sessions[session_id]
        return ChatResponse(
            reply="يا هلا فيك بمتجر سمارت ستور! تفضل، كيف بقدر أساعدك اليوم؟",
            funnel_stage="greeting"
        )
        
    # Get or create session with TTL check
    session = user_sessions.get(session_id)
    if session:
        last_activity = session.get("last_activity", 0)
        if current_time - last_activity > SESSION_TIMEOUT:
            session = None
            
    if not session:
        session = {
            "messages": [],
            "funnel_stage": "greeting",
            "guardrail_passed": True,
            "last_activity": current_time
        }
        
    # Trim old messages (Sliding Window)
    messages_history = session["messages"]
    if len(messages_history) > MAX_MESSAGES:
        messages_history = messages_history[-MAX_MESSAGES:]
        
    new_input = {
        "messages": messages_history + [HumanMessage(content=user_text)],
        "funnel_stage": session.get("funnel_stage", "greeting"),
        "guardrail_passed": True
    }
    
    # Retry logic for rate limit errors
    import time as _time
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            new_state = agent_graph.invoke(new_input)
            break
        except Exception as e:
            error_msg = str(e)
            print(f"[API Error] Attempt {attempt+1}: {error_msg[:150]}")
            if "429" in error_msg and attempt < max_retries:
                _time.sleep(3)  # Wait 3 seconds before retry
                continue
            return ChatResponse(
                reply="عذراً، صار ضغط على السيرفر. جرب مرة ثانية بعد شوي!",
                funnel_stage=session.get("funnel_stage", "greeting")
            )
    
    # Update session
    new_state["last_activity"] = current_time
    user_sessions[session_id] = new_state
    
    last_msg = new_state["messages"][-1]
    reply_text = last_msg.content
    funnel_stage = new_state.get("funnel_stage", "greeting")
    
    # Find the most recent product search results
    products = []
    for msg in reversed(new_state["messages"]):
        if getattr(msg, "name", None) == "search_store_products":
            try:
                products = json.loads(msg.content)
            except:
                pass
            break
        elif getattr(msg, "type", None) == "human":
            break
            
    return ChatResponse(
        reply=reply_text,
        products=products if products else None,
        funnel_stage=funnel_stage
    )
