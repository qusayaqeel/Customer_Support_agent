from fastapi import FastAPI
from dotenv import load_dotenv

# 1. Load environment variables (API Keys) before importing other modules
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
from core.rag import init_vector_store
from db.database import init_db

# 2. Initialize databases once at server startup
print("Initializing databases...")
init_vector_store("data/products.json", "chroma_db")
init_db("orders.db")

# 3. Create FastAPI application
app = FastAPI(title="Customer Support AI Agent")

# Add CORS middleware to allow React frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Register API routers
app.include_router(chat_router)

@app.get("/")
def root():
    """Simple health check endpoint to verify server is running."""
    return {"message": "Customer Support AI Agent Backend is running!"}
