"""
Vector Store Service (ChromaDB) for Retrieval-Augmented Generation (RAG).
Replaces legacy FAISS implementation with a persistent, production-ready vector DB.
"""
from __future__ import annotations
import os
import uuid
import chromadb
from chromadb.config import Settings

from app.core.config import settings
from app.core.logging_config import get_logger
from app.ml.embedding_service import embedding_service

logger = get_logger(__name__)


class CustomEmbeddingFunction(chromadb.EmbeddingFunction):
    """Bridge ChromaDB embedding interface to our cached EmbeddingService."""
    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        embeddings = []
        for text in input:
            emb = embedding_service.get_embedding(text)
            if emb is None:
                # Provide a zero vector if embedding fails to keep Chroma happy
                logger.warning("Falling back to zero vector for chunk")
                emb = [0.0] * 384  # Assuming MiniLM-L6-v2 dim
            embeddings.append(emb)
        return embeddings


class VectorStore:
    def __init__(self):
        # Initialize persistent ChromaDB
        db_path = os.path.join(os.getcwd(), "chroma_db")
        os.makedirs(db_path, exist_ok=True)
        
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.embed_fn = CustomEmbeddingFunction()
            
            # Collection for resume chunks (Document Q&A)
            self.resume_chunks = self.client.get_or_create_collection(
                name="resume_chunks",
                embedding_function=self.embed_fn,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Collection for full resumes profiles (Job Matching)
            self.resume_profiles = self.client.get_or_create_collection(
                name="resume_profiles",
                embedding_function=self.embed_fn,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("ChromaDB initialized successfully at %s", db_path)
        except Exception as exc:
            logger.error("Failed to initialize ChromaDB: %s", exc)
            self.client = None

    def add_resume_chunks(self, resume_id: str, chunks: list[str], metadatas: list[dict]):
        """Add document chunks to the resume_chunks collection for RAG."""
        if not self.client or not chunks:
            return
            
        ids = [f"{resume_id}_chunk_{i}" for i in range(len(chunks))]
        # Inject resume_id into metadata
        for meta in metadatas:
            meta["resume_id"] = resume_id
            
        try:
            self.resume_chunks.upsert(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            logger.info("Upserted %d chunks for resume %s", len(chunks), resume_id)
        except Exception as exc:
            logger.error("Failed to upsert chunks: %s", exc)

    def search_resume_chunks(self, resume_id: str, query: str, n_results: int = 5) -> list[dict]:
        """Retrieve relevant chunks from a specific resume for Q&A."""
        if not self.client:
            return []
            
        try:
            results = self.resume_chunks.query(
                query_texts=[query],
                n_results=n_results,
                where={"resume_id": resume_id}
            )
            
            hits = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    hits.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else 0.0
                    })
            return hits
        except Exception as exc:
            logger.error("Error querying resume chunks: %s", exc)
            return []

    def add_resume_profile(self, resume_id: str, user_id: str, profile_text: str, metadata: dict):
        """Add a full candidate profile for job matching search."""
        if not self.client or not profile_text:
            return
            
        meta = metadata.copy()
        meta.update({"resume_id": resume_id, "user_id": user_id})
        
        try:
            self.resume_profiles.upsert(
                documents=[profile_text],
                metadatas=[meta],
                ids=[resume_id]
            )
        except Exception as exc:
            logger.error("Failed to upsert resume profile: %s", exc)

    def search_candidates(self, job_description: str, n_results: int = 10) -> list[dict]:
        """Find the best resumes matching a job description."""
        if not self.client:
            return []
            
        try:
            results = self.resume_profiles.query(
                query_texts=[job_description],
                n_results=n_results
            )
            
            hits = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    hits.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else 0.0
                    })
            return hits
        except Exception as exc:
            logger.error("Error searching candidates: %s", exc)
            return []


# Singleton
vector_store = VectorStore()
