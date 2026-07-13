from typing import List, Dict, Any
import numpy as np
from app.ml.ner import NERService
from app.ml.vector_search import VectorSearchService
from app.services.ml_service import _get_sentence_model
from app.ml.llm_service import ai_llm_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class AnalyticsEngine:
    def __init__(self):
        self.ner = NERService()
        self.vector_db = VectorSearchService()
        self.model = _get_sentence_model()

    async def analyze_full_profile(self, resume_text: str, target_role: str) -> Dict[str, Any]:
        """
        Phase 3/4/6 implementation: Extraction -> Embedding -> LLM Insights
        """
        # 1. Extraction (spacy)
        skills = self.ner.extract_skills(resume_text)
        entities = self.ner.extract_entities(resume_text)
        
        # 2. Semantic Embedding (sentence-transformers)
        embedding = None
        if self.model:
            embedding = self.model.encode(resume_text, normalize_embeddings=True)
            
        # 3. LLM Insights (Phase 6)
        review_prompt = f"Resume Review for {target_role}: {resume_text[:2000]}"
        insights = await ai_llm_service.generate_response(review_prompt)
        
        # 4. Scoring (Simplified for this module)
        score = 85.0 # Logic would go here
        
        return {
            "overall_score": score,
            "extracted_skills": skills,
            "entities": entities,
            "ai_insights": insights,
            "embedding": embedding.tolist() if embedding is not None else None
        }

analytics_engine = AnalyticsEngine()
