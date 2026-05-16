# Smart Store AI Agent - Project State

## Project Overview
A Telegram/Web AI chatbot acting as a Palestinian electronics salesman called "Abu Al-Abd" for "Smart Store".
Uses RAG for product search and LangGraph as a State Machine for conversation flow management.

---

## Tech Stack
| Technology | Usage |
|---|---|
| **LangGraph** | State Machine for conversation flow (Nodes + Edges) |
| **LangChain** | LLM Integration + Tool Binding |
| **OpenRouter** | Primary LLM Provider (Gemini 2.0 Flash) |
| **Groq** | Fallback LLM Provider (Llama 4 Maverick) |
| **ChromaDB** | Vector Database for semantic product search (RAG) |
| **FastAPI** | API Server |
| **SQLite** | Orders database |
| **React + Vite** | Web frontend (chat UI + product cards) |

---

## Project Structure
```
Customer_Support_agent/
├── main.py                  # Entry point - FastAPI + DB initialization
├── requirements.txt         # Dependencies
├── .env                     # API keys (OPENROUTER_API_KEY, GROQ_API_KEY)
│
├── agent/                   # AI Agent layer (LangGraph)
│   ├── state.py             # AgentState: messages + funnel_stage + guardrail_passed
│   ├── nodes.py             # Nodes: input_guardrail → chatbot → output_guardrail
│   ├── graph.py             # Graph: wiring nodes and conditional edges
│   └── tools.py             # LangChain tools: search_store_products + save_customer_order
│
├── api/
│   ├── chat.py              # REST API endpoint for web frontend
│   └── webhook.py           # Telegram Webhook (optional)
│
├── core/
│   └── rag.py               # ChromaDB: init_vector_store + search_products (Strict RAG)
│
├── db/
│   └── database.py          # SQLite: init_db + save_order
│
├── data/
│   └── products.json        # Product catalog (20 products)
│
├── frontend/                # React (Vite) web frontend
│
├── tests/                   # Test suite (guardrails, RAG, DB, integration, pipeline, hallucination)
│
└── chroma_db/               # Vector database (auto-rebuilt from products.json)
```

---

## Architecture
```
User Message (Web / Telegram)
      │
      ▼
  [FastAPI] → Session Management (Sliding Window + TTL)
      │
      ▼
  [input_guardrail] → Programmatic check (Regex): Prompt Injection + Off-Topic
      │
  ┌───┴───┐
  │ Safe? │
  └───┬───┘
   Yes│    No → Auto-reply → END
      ▼
  [chatbot] → LLM with System Prompt + Sales Funnel Stage
      │
  ┌───┴────┐
  │ Tool?  │
  └───┬────┘
   Yes│    No
      ▼      ▼
  [tools] [output_guardrail] → Price validation → END
      │
      ▼
  [chatbot] → Reads tool results → responds
      │
      ▼
  [output_guardrail] → Final check → END
```

---

## Current Status ✅
- [x] LangGraph State Machine with 4 nodes
- [x] Input Guardrail: Prompt Injection protection (Regex)
- [x] Output Guardrail: Active Context State (price validation against search results)
- [x] Strict RAG: Similarity distance filtering (threshold 1.2) + keyword fallback
- [x] Sales Funnel: greeting → discovery → pitching → closing
- [x] System Prompt in Palestinian dialect with 8 sections
- [x] Product catalog: 20 diverse products (phones, laptops, audio, watches, accessories)
- [x] Tool Output Formatting: stock hidden from search results
- [x] ChromaDB rebuilt from products.json on first run
- [x] Multi-Model Failover: Gemini Flash (OpenRouter) → Maverick (Groq)
- [x] Web Frontend: React + Vite with glassmorphism dark theme
- [x] REST API: /api/chat endpoint with session management
- [x] Code cleanup: all comments converted to English
- [x] Professional README in English

---

## Known Issues & Planned Improvements 🔧

### Issue 1: Product Hallucination (Pre-trained Knowledge Leakage)
**Description:** The model sometimes invents products not in the database (e.g., Dell Inspiron 3000 with code p101) or suggests products from wrong categories (asked for laptop, suggests keyboard).
**Status:** Output Guardrail + Strict RAG + Prompt rules built. Needs comprehensive testing.
**Related files:** `agent/nodes.py` (output_guardrail), `core/rag.py` (max_distance), `agent/tools.py` (formatting)

### Issue 2: Unnatural Response Style
**Description:** The model sometimes responds with long replies or uses Egyptian/Standard Arabic instead of Palestinian dialect.
**Proposed fix:** Few-shot examples in the Prompt + Post-processing

### Issue 3: Conversation Flow Validation
**Description:** Need to design and validate the complete conversation workflow - what happens when users go off-script, skip steps, or take unexpected paths.
**Proposed fix:** Draw complete workflow diagram, identify edge cases, implement validation for each state transition.

### Issue 4: Structured Output + Frontend Product Cards
**Description:** Instead of sending long text, the model should:
- Return structured JSON (product_id + short_pitch)
- The frontend builds product cards with "Buy" and "Details" buttons
**Related files:** `api/chat.py`, `agent/nodes.py`, `frontend/src/App.jsx`

### Issue 5: Memory Management Improvements
**Description:** Sessions in `user_sessions` (RAM) need better management:
- Persist sessions across server restarts
- Better sliding window that preserves tool call context
**Related files:** `api/chat.py`, `api/webhook.py`

---

## Environment Variables (.env)
```
OPENROUTER_API_KEY=...
GROQ_API_KEY=...
TELEGRAM_BOT_TOKEN=... (optional, for Telegram integration)
```

## Running the Project
```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend
uvicorn main:app --reload

# Start the frontend
cd frontend && npm install && npm run dev

# Run tests (fast, no LLM)
pytest tests/test_guardrails.py tests/test_rag.py tests/test_database.py -v
```
