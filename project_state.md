# Project State

## Session Resumption Point (نقطة الانطلاق للجلسة القادمة)
- **Next Task:** Start implementing the AI Brain `run_agent_loop(...)` in `core/agent.py` using TDD.
- **Prerequisite:** Ensure a Google Gemini API Key is available in the `.env` file to start connecting with the AI model.

## System Architecture & Libraries
- **LLM**: Gemini 1.5 Flash (Google AI Studio) for text generation and Function Calling.
- **Embeddings**: `nomic-embed-text` via Ollama (Currently using default ChromaDB for TDD phase).
- **Vector DB**: ChromaDB (Local).
- **Backend Framework**: FastAPI.
- **Database**: SQLite.
- **Integration**: Telegram Bot API via ngrok.
- **Core Logic**: Raw Python (No LangChain/LangGraph) with strict TDD.

## Completed Functions Blueprint
| Function/API Name | Target File/Module | Purpose |
| --- | --- | --- |
| `load_products()` / `init_vector_store()` | `core/rag.py` | Initialize ChromaDB with fake products. |
| `search_products(query)` | `core/rag.py` | Semantic search in ChromaDB. |
| `init_db()` | `db/database.py` | Create SQLite tables. |
| `save_order(...)` | `db/database.py` | Function for AI to call to save an order. |

## Pending Functions Blueprint
| Function/API Name | Target File/Module | Purpose |
| --- | --- | --- |
| `run_agent_loop(...)` | `core/agent.py` | Gemini API interaction loop. |
| `telegram_webhook()` | `api/webhook.py` | FastAPI endpoint for Telegram. |
| `send_message(...)` | `api/webhook.py` | Send message back via Telegram API. |

## Technical Decisions
- Using Raw Python for deep understanding of AI Agent loops.
- `products.json` will serve as the initial mock data source.
- TDD approach: Each function will have a test before implementation.
- API Testing will be done using Apidog. Server via uvicorn.
