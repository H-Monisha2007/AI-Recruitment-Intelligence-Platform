"""
Retrieval-Augmented Generation (RAG) Pipeline.
Handles document chunking, semantic retrieval, and context-aware generation.
"""
from __future__ import annotations
import json
from typing import Any

from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.logging_config import get_logger
from app.ml.vector_store import vector_store
from app.ml.llm_service import ai_llm_service

logger = get_logger(__name__)

class RAGPipeline:
    def __init__(self):
        # Setup modern text chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_and_store_resume(self, resume_id: str, text: str, user_id: str):
        """Chunk resume text and store in Vector DB for Q&A."""
        logger.info("Starting RAG processing for resume %s", resume_id)
        
        # 1. Chunking
        chunks = self.text_splitter.split_text(text)
        
        # 2. Metadata generation
        metadatas = [
            {"chunk_index": i, "user_id": user_id, "source": "resume"} 
            for i in range(len(chunks))
        ]
        
        # 3. Store chunks in ChromaDB
        vector_store.add_resume_chunks(resume_id, chunks, metadatas)
        
        # 4. Store full profile (First 5000 chars to avoid token limits)
        vector_store.add_resume_profile(
            resume_id=resume_id, 
            user_id=user_id, 
            profile_text=text[:5000],
            metadata={"status": "active"}
        )
        
        logger.info("Stored %d chunks for resume %s", len(chunks), resume_id)

    async def query_resume(self, resume_id: str, question: str) -> str:
        """RAG Q&A over a specific candidate's resume."""
        if not ai_llm_service.is_active:
            return "AI Q&A is currently disabled. (Missing API Key)"
            
        # 1. Retrieve most relevant chunks
        hits = vector_store.search_resume_chunks(resume_id, question, n_results=4)
        
        if not hits:
            return "I couldn't find relevant information in this resume to answer your question."
            
        # 2. Construct context
        context = "\n\n---\n\n".join([hit["content"] for hit in hits])
        
        # 3. Prompt Construction
        system_prompt = (
            "You are an expert technical recruiter and AI assistant. "
            "Use the provided context from a candidate's resume to answer the question. "
            "If the answer is not contained in the context, say 'I don't have enough information in the resume to answer this'. "
            "Keep your answer concise and professional."
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}"
        
        # 4. Generate
        return await ai_llm_service.generate_response(f"{system_prompt}\n\n{user_prompt}")
        
    async def parse_resume_structured(self, resume_text: str) -> dict[str, Any]:
        """Extract a structured Knowledge Model from a Resume using LLM."""
        if not ai_llm_service.is_active:
            return {"error": "LLM extraction disabled"}
            
        system_prompt = """
        You are an advanced AI resume parser. Your job is to extract highly structured data from a resume text.
        You must output ONLY valid JSON matching this schema:
        {
          "personal_info": {"name": "", "email": "", "phone": "", "linkedin": "", "github": ""},
          "summary": "",
          "skills": {
            "languages": [],
            "frameworks": [],
            "cloud_platforms": [],
            "databases": [],
            "soft_skills": []
          },
          "experience": [
            {
              "company": "",
              "title": "",
              "duration": "",
              "highlights": []
            }
          ],
          "education": [
            {
              "institution": "",
              "degree": "",
              "year": ""
            }
          ],
          "projects": []
        }
        """
        
        user_prompt = f"Resume Text to parse:\n\n{resume_text[:15000]}"
        return await ai_llm_service.generate_structured(system_prompt, user_prompt)

# Singleton
rag_pipeline = RAGPipeline()
