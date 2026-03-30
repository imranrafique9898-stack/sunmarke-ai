"""
Embeddings and RAG (Retrieval-Augmented Generation) service
Handles embedding generation, storage, and retrieval
"""

import json
import os
from typing import List, Tuple
from sqlalchemy.orm import Session
from database import Document, DocumentChunk, USE_POSTGRES, HAS_PGVECTOR
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np

# Free local embeddings using sentence-transformers (no API key needed)
_embedding_model = None

def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

# Embedding configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Free local model, no API key needed
EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 output size
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
TOP_K = 8  # Number of chunks to retrieve


class EmbeddingsService:
    """Handle embeddings generation and storage"""

    @staticmethod
    def get_embedding(text: str) -> List[float]:
        try:
            model = _get_embedding_model()
            embedding = model.encode(text.strip(), normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * EMBEDDING_DIMENSION

    @staticmethod
    def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """
        Split text into overlapping chunks
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_text(text)
        return chunks


class RAGService:
    """Retrieval-Augmented Generation service"""

    def __init__(self, db: Session):
        self.db = db
        self.embeddings = EmbeddingsService()

    def load_and_index_documents(self, json_file: str = "scraped-data.json"):
        """
        Load documents from JSON file and create embeddings
        Call this once to populate the vector database
        """
        print("📥 Loading documents from JSON...")
        
        # Get the correct path
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_path, json_file)
        
        if not os.path.exists(json_path):
            print(f"❌ File not found: {json_path}")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        total_chunks = 0

        for item in data:
            url = item['url']
            title = item['title']
            content = item['content']
            section = item['section']

            # Skip if already indexed
            existing = self.db.query(Document).filter(Document.url == url).first()
            if existing:
                print(f"⏭️  Skipping (already indexed): {url}")
                continue

            # Save document
            doc = Document(
                url=url,
                title=title,
                section=section,
                content=content
            )
            self.db.add(doc)
            self.db.flush()  # Get the ID

            # Chunk the content
            chunks = self.embeddings.chunk_text(content)
            print(f"📄 {title} ({len(chunks)} chunks)")

            # Create embeddings and save chunks
            for idx, chunk in enumerate(chunks):
                try:
                    embedding = self.embeddings.get_embedding(chunk)
                    
                    # For SQLite, store embedding as JSON string
                    # For PostgreSQL, store as Vector
                    if not (USE_POSTGRES and HAS_PGVECTOR):
                        embedding = json.dumps(embedding)
                    
                    chunk_obj = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=idx,
                        text=chunk,
                        embedding=embedding,
                        section=section,
                        url=url
                    )
                    self.db.add(chunk_obj)
                    total_chunks += 1

                except Exception as e:
                    print(f"❌ Error processing chunk {idx}: {e}")

            self.db.commit()

        print(f"\n✅ Indexed {len(data)} documents with {total_chunks} chunks")

    def retrieve_context(self, query: str, top_k: int = TOP_K) -> Tuple[List[dict], List[str]]:
        """
        Retrieve most relevant chunks based on query using semantic search
        Returns: (chunks, sources)
        """
        # Get embedding for query
        query_embedding = self.embeddings.get_embedding(query)

        try:
            if USE_POSTGRES and HAS_PGVECTOR:
                # Use pgvector for PostgreSQL
                results = self.db.query(
                    DocumentChunk.text,
                    DocumentChunk.url,
                    DocumentChunk.section,
                ).order_by(
                    DocumentChunk.embedding.cosine_distance(query_embedding)
                ).limit(top_k).all()
            else:
                # Use Python-based cosine similarity for SQLite
                all_chunks = self.db.query(
                    DocumentChunk.id,
                    DocumentChunk.text,
                    DocumentChunk.url,
                    DocumentChunk.section,
                    DocumentChunk.embedding
                ).all()
                
                # Calculate similarity scores
                scored_results = []
                query_embedding_arr = np.array(query_embedding)
                
                for chunk_id, text, url, section, embedding_data in all_chunks:
                    # Parse embedding from JSON if stored as string
                    if isinstance(embedding_data, str):
                        try:
                            embedding_arr = np.array(json.loads(embedding_data))
                        except:
                            continue
                    else:
                        embedding_arr = np.array(embedding_data if hasattr(embedding_data, '__iter__') else [0.0] * EMBEDDING_DIMENSION)
                    
                    # Cosine similarity
                    norm_query = np.linalg.norm(query_embedding_arr)
                    norm_embedding = np.linalg.norm(embedding_arr)
                    
                    if norm_query > 0 and norm_embedding > 0:
                        similarity = np.dot(query_embedding_arr, embedding_arr) / (norm_query * norm_embedding)
                        scored_results.append((similarity, text, url, section))
                
                # Sort by similarity and get top_k
                scored_results.sort(key=lambda x: x[0], reverse=True)
                top = scored_results[:top_k]
                if top:
                    print(f"🔍 Top similarity score: {top[0][0]:.4f} | chunk: {top[0][1][:80]}")
                results = [(text, url, section) for _, text, url, section in top]

            # Return chunks as dicts with url attached
            chunks = [{"text": r[0], "url": r[1], "section": r[2]} for r in results]
            sources = list(dict.fromkeys(r[1] for r in results))  # unique URLs

            return chunks, sources

        except Exception as e:
            print(f"❌ Error retrieving context: {e}")
            return [], []

    def build_context_string(self, chunks: List[dict]) -> str:
        parts = []
        for c in chunks:
            parts.append(f"[Source: {c['url']}]\n{c['text']}")
        return "\n\n---\n\n".join(parts)

    def generate_rag_prompt(self, query: str, context: str) -> str:
        prompt = f"""You are a helpful assistant for Sunmarke School. Answer the user's question using the context below.

CONTEXT FROM SCHOOL WEBSITE (each section includes its source URL):
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
- Answer based on the context above. Be specific and helpful.
- You MUST always include the relevant source URL(s) as clickable markdown links at the end of your answer, like: [View on Sunmarke website](https://...)
- If multiple sources are relevant, include all their links.
- If the context has partial info, use it and still provide the link.
- Only say you don't know if there is truly no relevant information.

ANSWER:"""
        return prompt


# ----- Helper function to initialize everything -----

def initialize_rag(db: Session):
    """
    Initialize RAG system by loading documents and creating embeddings
    Call this once when the backend starts
    """
    rag = RAGService(db)
    
    # Check if already indexed
    doc_count = db.query(Document).count()
    if doc_count == 0:
        print("\n🚀 Initializing RAG system...")
        rag.load_and_index_documents()
    else:
        print(f"✅ RAG system already initialized ({doc_count} documents)")
    
    return rag
