"""
LLM Service — actual integration with Google Gemini via LangChain.
Replaces the mock implementation.
"""
from __future__ import annotations
import os
import json
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class LLMService:
    def __init__(self):
        # We need an API key for Google Gemini
        # It should be set in environment as GOOGLE_API_KEY
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.is_active = bool(self.api_key)
        
        if self.is_active:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    temperature=0.2,
                    google_api_key=self.api_key
                )
                logger.info("Google Gemini LLM connected successfully.")
            except Exception as exc:
                logger.error("Failed to initialize Google Gemini: %s", exc)
                self.is_active = False
                self.llm = None
        else:
            logger.warning("No GOOGLE_API_KEY found. LLM functionality is disabled/mocked.")
            self.llm = None

    async def generate_response(self, prompt: str) -> str:
        """Base text generation."""
        if not self.is_active or not self.llm:
            return "LLM integration is disabled. Please provide GOOGLE_API_KEY."
            
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as exc:
            logger.error("LLM Generation failed: %s", exc)
            return f"Error connecting to AI Provider: {str(exc)}"

    async def generate_structured(self, system_prompt: str, user_prompt: str, output_schema: type | dict = None) -> dict[str, Any]:
        """
        Generates a structured JSON response using Gemini's JSON mode.
        """
        if not self.is_active or not self.llm:
            return {"error": "LLM not configured"}

        try:
            # Enforce JSON output format explicitly in the prompt
            format_instructions = "You MUST return a valid JSON object. Do not include markdown formatting like ```json or ```."
            
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "{system_prompts}\n{format}"),
                ("user", "{user_prompts}")
            ])
            
            # Using ChatGoogleGenerativeAI with response_mime_type="application/json"
            # Some versions of langchain-google-genai support this natively via bind.
            try:
                json_llm = self.llm.bind(response_mime_type="application/json")
            except AttributeError:
                json_llm = self.llm
                
            chain = prompt_template | json_llm | StrOutputParser()
            
            result_str = await chain.ainvoke({
                "system_prompts": system_prompt,
                "format": format_instructions,
                "user_prompts": user_prompt
            })
            
            # Clean up markdown if the LLM leaked it despite instructions
            result_str = result_str.strip()
            if result_str.startswith("```json"):
                result_str = result_str[7:]
            if result_str.startswith("```"):
                result_str = result_str[3:]
            if result_str.endswith("```"):
                result_str = result_str[:-3]
                
            return json.loads(result_str.strip())
            
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM response into JSON: %s\nResponse: %s", exc, result_str)
            return {"error": "Invalid output format from LLM"}
        except Exception as exc:
            logger.error("Structured LLM Generation failed: %s", exc)
            return {"error": str(exc)}
            
    async def extract_skills(self, resume_text: str) -> list[str]:
        """Fallback dynamic skill extraction if NER fails."""
        sys_prompt = "You are an expert technical recruiter AI. Extract a categorized list of professional skills, programming languages, and tools from the provided resume text."
        user_prompt = f"Resume Text:\n{resume_text}\n\nReturn ONLY a JSON array of strings, for example: [\"Python\", \"React\", \"AWS\"]."
        
        result = await self.generate_structured(sys_prompt, user_prompt)
        if isinstance(result, list):
            return result
        # If it returned a dict wrapper like {"skills": [...]}
        if isinstance(result, dict):
            for val in result.values():
                if isinstance(val, list):
                    return val
        return []


ai_llm_service = LLMService()
