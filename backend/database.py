"""
Database configuration with PGVector for embeddings
Falls back to SQLite if PostgreSQL is not available
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, func, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import json

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/sunmarke_ai"
)

# Try to use pgvector, fall back to storing embeddings as text
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

# Determine if using PostgreSQL
USE_POSTGRES = DATABASE_URL.startswith("postgresql")

# Create engine with fallback to SQLite
if USE_POSTGRES:
    try:
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        # Test connection
        with engine.connect() as conn:
            pass
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"⚠️  PostgreSQL connection failed: {e}")
        print("📦 Falling back to SQLite for local development...")
        engine = create_engine(
            "sqlite:///./sunmarke_ai.db",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        USE_POSTGRES = False
        HAS_PGVECTOR = False
else:
    # Use SQLite
    engine = create_engine(
        "sqlite:///./sunmarke_ai.db",
        echo=False,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# ----- Database Models -----

class Document(Base):
    """Store raw documents from scraped content"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1000), unique=True, index=True)
    title = Column(String(500))
    section = Column(String(100), index=True)  # about, curriculum, admissions, etc.
    content = Column(String(50000))  # Raw text content
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentChunk(Base):
    """Store chunked content with embeddings"""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)  # Reference to Documents
    chunk_index = Column(Integer)  # Order of chunk within document
    text = Column(String(5000))  # Chunk content
    # For PostgreSQL: Vector(1536), For SQLite: Text (stores JSON array)
    embedding = Column(Vector(1536) if (USE_POSTGRES and HAS_PGVECTOR) else Text)  # OpenAI embedding (1536 dimensions)
    section = Column(String(100), index=True)
    url = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # Index for semantic search
        # CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    )


class Query(Base):
    """Store user queries and responses for logging"""
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(String(1000))
    transcribed_text = Column(String(1000))
    
    # Responses from 3 models
    gemini_response = Column(String(5000))
    kimi_response = Column(String(5000))
    deepseek_response = Column(String(5000))
    
    # Metadata
    retrieved_chunks = Column(Integer)  # Number of relevant chunks
    response_time = Column(Float)  # Milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)


# ----- Database Setup -----

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
