"""
FastAPI entry point for the SHL Assessment Recommender.

Exposes:
  GET  /health  → {"status": "ok"}
  POST /chat    → ChatResponse (stateless conversation)
"""
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.catalog_loader import load_catalog
from app.retriever import CatalogRetriever
from app.agent import generate_reply
from app.schemas import ChatRequest, ChatResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Conversational SHL Assessment Recommender",
    description="Stateless conversational API for SHL Individual Test Solutions selection.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup: load catalog and build retriever ─────────────────────────────────
try:
    catalog = load_catalog()
    retriever = CatalogRetriever(catalog)
    logger.info(f"Catalog loaded: {len(catalog)} items indexed.")
except Exception as e:
    logger.error(f"Failed to load catalog: {e}")
    catalog = []
    retriever = None  # type: ignore


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Stateless conversational chat endpoint.

    Accepts full message history and returns the next assistant reply
    with optional SHL catalog recommendations.
    """
    if retriever is None:
        raise HTTPException(
            status_code=503,
            detail="Catalog not loaded. Check backend/data/shl_catalog.json.",
        )

    try:
        reply, recommendations, end_of_conversation = generate_reply(
            request.messages, retriever
        )
    except Exception as e:
        logger.error(f"Error in generate_reply: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal agent error.")

    return ChatResponse(
        reply=reply,
        recommendations=recommendations,
        end_of_conversation=end_of_conversation,
    )
