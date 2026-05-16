import os
import requests
import time
from fastapi import APIRouter, Request, BackgroundTasks
from langchain_core.messages import HumanMessage
from agent.graph import agent_graph

router = APIRouter()

# In-memory session storage
user_sessions = {}
SESSION_TIMEOUT = 30 * 60  # 30 minutes
MAX_MESSAGES = 20  # Keep last 20 messages only (10 back-and-forth)

def send_telegram_message(chat_id: int, text: str):
    """Send a message to Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

def process_telegram_update(chat_id: int, user_text: str):
    """Process Telegram messages with session management (sliding window + TTL)."""
    current_time = time.time()
    
    # 1. Reset session on /start command
    if user_text.strip() == "/start":
        if chat_id in user_sessions:
            del user_sessions[chat_id]
        send_telegram_message(chat_id, "يا هلا فيك بمتجر سمارت ستور! أنا أبو العبد، تفضل كيف بقدر أساعدك اليوم؟")
        return

    # 2. Get current session
    session = user_sessions.get(chat_id)
    
    # 3. Check session TTL (expiry)
    if session:
        last_activity = session.get("last_activity", 0)
        if current_time - last_activity > SESSION_TIMEOUT:
            print(f"Session expired for {chat_id}. Creating new session.")
            session = None
            
    if not session:
        session = {
            "messages": [],
            "funnel_stage": "greeting",
            "guardrail_passed": True,
            "last_activity": current_time
        }
        
    try:
        # 4. Trim old messages (Sliding Window)
        messages_history = session["messages"]
        if len(messages_history) > MAX_MESSAGES:
            messages_history = messages_history[-MAX_MESSAGES:]
            
        # 5. Prepare input
        new_input = {
            "messages": messages_history + [HumanMessage(content=user_text)],
            "funnel_stage": session.get("funnel_stage", "greeting"),
            "guardrail_passed": True
        }
        
        # 6. Run the LangGraph agent
        new_state = agent_graph.invoke(new_input)
        
        # 7. Update session memory
        new_state["last_activity"] = current_time
        user_sessions[chat_id] = new_state
        
        # 8. Extract and send response
        response_text = new_state["messages"][-1].content
        send_telegram_message(chat_id, response_text)
        
    except Exception as e:
        print(f"Agent Graph Error: {e}")
        send_telegram_message(chat_id, "عذراً، أواجه مشكلة تقنية حالياً. يرجى المحاولة لاحقاً.")

@router.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Telegram webhook endpoint - receives incoming messages from Telegram.
    Processes in background to immediately return 200 OK (prevents Telegram retries).
    """
    data = await request.json()
    
    # Ensure the update contains a text message
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]
        
        # Process in background so Telegram gets immediate 200 OK response
        background_tasks.add_task(process_telegram_update, chat_id, user_text)
        
    return {"status": "ok"}
