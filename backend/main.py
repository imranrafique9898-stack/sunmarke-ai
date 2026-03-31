"""
FastAPI Backend - Main Application
Orchestrates RAG, embeddings, and LLM responses
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import asyncio
import json
import time
import os
from dotenv import load_dotenv

from database import init_db, get_db, Query
from rag_service import RAGService, initialize_rag
from llm_service import LLMService

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Sunmarke AI Voice Agent API",
    description="RAG-based voice agent with 3 LLM models",
    version="1.0.0"
)

# Add CORS middleware  
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG service
rag_service = None

# ----- Pydantic Models -----

class QueryRequest(BaseModel):
    """User query request"""
    query: str
    transcribed_text: str = None  # Optional: transcribed voice text


class RAGResponse(BaseModel):
    """RAG retrieval response"""
    context: str
    sources: list[str]
    chunks_count: int


class LLMResponses(BaseModel):
    """Responses from all 3 LLMs"""
    gemini: str
    kimi: str
    deepseek: str


class QueryResponse(BaseModel):
    """Complete response with RAG context and LLM outputs"""
    query: str
    rag: RAGResponse
    responses: LLMResponses
    response_time_ms: float
    

# ----- API Endpoints -----

@app.on_event("startup")
async def startup_event():
    """Initialize database and RAG system on startup"""
    global rag_service
    
    print("\n" + "="*60)
    print("🚀 SUNMARKE AI VOICE AGENT - STARTING UP")
    print("="*60)
    
    # Initialize database tables
    from database import engine, USE_POSTGRES
    init_db()
    
    if not USE_POSTGRES:
        print("ℹ️  Using SQLite for local development")
    
    # Get database session and initialize RAG
    from database import SessionLocal
    db = SessionLocal()
    try:
        # Don't automatically load documents if they don't exist yet
        # This is intentional for local development
        from database import Document
        doc_count = db.query(Document).count()
        if doc_count > 0:
            rag_service = initialize_rag(db)
        else:
            from rag_service import RAGService
            rag_service = RAGService(db)
            print("⚠️  No documents indexed. Call /api/load-documents to index data.")
        
        print("\n✅ Backend initialized successfully!\n")
    except Exception as e:
        print(f"⚠️  Warning during startup: {e}")
        print("✅ Backend initialized (with limitations)\n")
    finally:
        db.close()


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Sunmarke AI Voice Agent",
        "ready": rag_service is not None
    }


@app.post("/api/query", response_model=QueryResponse, tags=["Query"])
async def process_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
) -> QueryResponse:
    """
    Process a user query through RAG + 3 LLMs
    
    1. Retrieve relevant context from vector database
    2. Generate responses from Gemini, Kimi, and DeepSeek
    3. Return all responses
    """
    start_time = time.time()
    
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        
        # Step 1: Retrieve context from vector database
        print(f"\n🔍 Query: {request.query}")
        chunks, sources = rag_service.retrieve_context(request.query, top_k=8)
        
        if not chunks:
            # If no context found, still try to answer from general knowledge
            print("⚠️  No relevant context found in knowledge base")
            context = "No specific information found in the school database."
        else:
            context = rag_service.build_context_string(chunks)
            print(f"✅ Retrieved {len(chunks)} relevant chunks")
        
        # Step 2: Build RAG prompt
        rag_prompt = rag_service.generate_rag_prompt(request.query, context)
        
        # Step 3: Get responses from all 3 LLMs in parallel
        print("🤖 Generating responses from 3 LLMs...")
        llm_responses = await LLMService.generate_all(rag_prompt)
        print("✅ All 3 LLM responses received")
        
        # Step 4: Log query and responses
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        query_record = Query(
            user_query=request.query,
            transcribed_text=request.transcribed_text or request.query,
            gemini_response=llm_responses['gemini'],
            kimi_response=llm_responses['kimi'],
            deepseek_response=llm_responses['deepseek'],
            retrieved_chunks=len(chunks),
            response_time=response_time
        )
        db.add(query_record)
        db.commit()
        
        # Step 5: Build response
        return QueryResponse(
            query=request.query,
            rag=RAGResponse(
                context=context[:500] + "..." if len(context) > 500 else context,  # Truncate for response
                sources=sources,
                chunks_count=len(chunks)
            ),
            responses=LLMResponses(
                gemini=llm_responses['gemini'],
                kimi=llm_responses['kimi'],
                deepseek=llm_responses['deepseek']
            ),
            response_time_ms=response_time
        )
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/stream", tags=["Query"])
async def stream_query(request: QueryRequest, db: Session = Depends(get_db)):
    """Stream responses from both LLMs token by token using SSE."""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")

    chunks, sources = rag_service.retrieve_context(request.query, top_k=8)
    context = rag_service.build_context_string(chunks) if chunks else "No specific information found."
    rag_prompt = rag_service.generate_rag_prompt(request.query, context)

    async def event_generator():
        import httpx
        api_key = os.getenv("GROQ_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        models = [("groq1", "llama-3.3-70b-versatile"), ("groq2", "gemma2-9b-it")]

        async def stream_model(label: str, model: str, queue: asyncio.Queue):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant for Sunmarke School."},
                    {"role": "user", "content": rag_prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": True,
            }
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions",
                                             headers=headers, json=payload) as resp:
                        async for line in resp.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data.strip() == "[DONE]":
                                    await queue.put(json.dumps({"model": label, "token": "", "done": True}) + "\n")
                                    return
                                try:
                                    chunk_data = json.loads(data)
                                    token = chunk_data["choices"][0]["delta"].get("content", "")
                                    if token:
                                        await queue.put(json.dumps({"model": label, "token": token, "done": False}) + "\n")
                                except Exception:
                                    pass
            except Exception as e:
                await queue.put(json.dumps({"model": label, "token": f"Error: {e}", "done": True}) + "\n")
            await queue.put(None)

        queues = [asyncio.Queue() for _ in models]
        tasks = [asyncio.create_task(stream_model(label, model, q)) for (label, model), q in zip(models, queues)]
        done = [False] * len(models)

        while not all(done):
            for i, queue in enumerate(queues):
                if done[i]:
                    continue
                try:
                    item = queue.get_nowait()
                    if item is None:
                        done[i] = True
                    else:
                        yield item
                except asyncio.QueueEmpty:
                    pass
            await asyncio.sleep(0.01)

        await asyncio.gather(*tasks)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/initialize", tags=["Admin"])
async def initialize_embeddings(db: Session = Depends(get_db)):
    """
    Initialize embeddings from scraped data
    This is called once to populate the vector database
    """
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        rag_service.load_and_index_documents()
        return {"status": "success", "message": "Embeddings initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", tags=["Admin"])
async def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    from database import Document, DocumentChunk, Query
    
    doc_count = db.query(Document).count()
    chunk_count = db.query(DocumentChunk).count()
    query_count = db.query(Query).count()
    
    return {
        "documents": doc_count,
        "chunks": chunk_count,
        "queries_processed": query_count,
        "embedding_dimension": 1536,
        "vector_db": "PostgreSQL + PGVector"
    }


# ----- Error Handlers -----

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))


# ----- Info Endpoint -----

@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Sunmarke AI Voice Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "query": "/api/query",
            "initialize": "/api/initialize",
            "stats": "/api/stats",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "technology": {
            "vector_db": "PostgreSQL + PGVector",
            "llms": ["Gemini", "Kimi (Moonshot)", "DeepSeek"],
            "orchestration": "FastAPI + Async"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"\n🚀 Starting server on port {port}...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
