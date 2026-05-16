# Smart Store AI Agent 🤖

An AI-powered customer support agent for **Smart Store** (سمارت ستور), a Palestinian electronics store. Built with **LangGraph** as a state machine, **ChromaDB** for RAG-based product search, and **FastAPI** as the backend. Features a React (Vite) web frontend for real-time chat.

The agent persona is "Abu Al-Abd" — a friendly, street-smart Palestinian electronics salesman who speaks in Palestinian Arabic dialect.

---

## Architecture

```
User Message (Web Frontend)
      │
      ▼
  [FastAPI /api/chat] → Session Management (Sliding Window + TTL)
      │
      ▼
  [input_guardrail] → Programmatic check (Regex): Prompt Injection + Off-Topic
      │
  ┌───┴───┐
  │ Safe? │
  └───┬───┘
   Yes│    No → Auto-reply → END
      ▼
  [chatbot] → LLM (Gemini Flash / Llama Maverick Failover)
      │
  ┌───┴────┐
  │ Tool?  │
  └───┬────┘
   Yes│    No
      ▼      ▼
  [tools] [output_guardrail] → Price validation against search results → END
      │
      ▼
  [chatbot] → Reads tool results and responds
      │
      ▼
  [output_guardrail] → Final price check → END
```

---

## Tech Stack

| Technology | Usage |
|---|---|
| **LangGraph** | State Machine for conversation flow (Nodes + Conditional Edges) |
| **LangChain** | LLM integration + Tool Binding |
| **OpenRouter** | Primary LLM Provider (Gemini 2.0 Flash) |
| **Groq** | Fallback LLM Provider (Llama 4 Maverick) |
| **ChromaDB** | Vector Database for semantic product search (RAG) |
| **FastAPI** | REST API backend |
| **SQLite** | Orders database |
| **React + Vite** | Web frontend (chat UI + product cards) |

---

## Project Structure

```
Customer_Support_agent/
├── main.py                  # Entry point - FastAPI + DB initialization
├── requirements.txt         # Python dependencies
├── .env                     # API keys (not committed)
├── .env.example             # Environment template
│
├── agent/                   # AI Agent layer (LangGraph)
│   ├── state.py             # AgentState: messages + funnel_stage + guardrail_passed
│   ├── nodes.py             # Nodes: input_guardrail → chatbot → output_guardrail
│   ├── graph.py             # Graph: wiring nodes and conditional edges
│   └── tools.py             # LangChain tools: search_store_products + save_customer_order
│
├── api/
│   ├── chat.py              # REST API endpoint for web frontend
│   └── webhook.py           # Telegram webhook (optional)
│
├── core/
│   └── rag.py               # ChromaDB: init_vector_store + search_products (Hybrid Search)
│
├── db/
│   └── database.py          # SQLite: init_db + save_order
│
├── data/
│   └── products.json        # Product catalog (20 products)
│
├── frontend/                # React (Vite) web frontend
│   ├── src/App.jsx          # Main chat + product card UI
│   └── src/App.css          # Glassmorphism dark theme
│
├── tests/                   # Test suite
│   ├── test_guardrails.py   # Unit tests: input/output guardrails (no LLM)
│   ├── test_rag.py          # Unit tests: vector store + semantic search
│   ├── test_database.py     # Unit tests: SQLite operations
│   ├── test_integration.py  # Integration tests with mock LLM
│   ├── test_pipeline_scenarios.py  # E2E tests with live LLM (20 scenarios)
│   └── test_hallucination_scenarios.py  # Hallucination trap tests (15 scenarios)
│
└── chroma_db/               # Vector database (auto-rebuilt from products.json)
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+ (for the frontend)
- API keys: OpenRouter and/or Groq

---

## How to Run

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up environment variables

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

```env
OPENROUTER_API_KEY=your_openrouter_key
GROQ_API_KEY=your_groq_key
```

### 3. Start the backend (FastAPI)

```bash
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`. ChromaDB and SQLite are auto-initialized on first run.

### 4. Start the frontend (React)

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173` and connect to the backend API.

---

## Running Tests

```bash
# Run fast tests only (no LLM calls, no token cost)
pytest tests/test_guardrails.py tests/test_rag.py tests/test_database.py tests/test_integration.py -v

# Run full pipeline tests (requires live LLM, consumes tokens)
pytest tests/test_pipeline_scenarios.py -v

# Run hallucination scenario tests
python tests/test_hallucination_scenarios.py
```

---

## Key Features

- **Multi-Model Failover**: Primary (Gemini 2.0 Flash via OpenRouter) → Fallback (Llama Maverick via Groq)
- **Input Guardrail**: Regex-based prompt injection detection + off-topic filtering (no LLM cost)
- **Output Guardrail**: Price validation against actual search results (blocks hallucinated prices)
- **Strict RAG**: Similarity distance threshold (1.2) + keyword fallback (hybrid search)
- **Sales Funnel**: greeting → discovery → pitching → closing
- **Session Management**: Sliding window (20 messages) + 30-minute TTL
- **Palestinian Dialect**: Natural conversational style with Palestinian Arabic
- **Product Catalog**: 20 products across 7 categories with Unsplash images