"""
Coordinator Agent — Orchestrates the Multi-Agent Evaluation System using LangGraph.
"""
from __future__ import annotations
from typing import Any, TypedDict, Literal

# Try importing from langgraph, gracefully degrade to fallback logic if not installed
def get_coordinator_app():
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        return None

    class AgentState(TypedDict):
        resume_text: str
        job_role: str
        job_profile: dict
        
        # Extracted state
        parsed_resume: dict
        extracted_skills: list[str]
        
        # Evaluation state
        ml_score: float
        skill_similarity: float
        semantic_score: float
        
        # Result state
        ats_score: float
        role_fit: float
        decision: str
        explanation: dict
        hire_prob: float
        confidence: float
        
        # RAG Feedback
        missing_skills: list[str]
        found_skills: list[str]
        top_roles: list[tuple[str, float]]

    # 1. Parsing Agent
    async def parser_node(state: AgentState) -> dict:
        from app.ml.rag_pipeline import rag_pipeline
        # In actual usage we would call the LLM to parse structured data
        # For performance in the pipeline if text is huge, we might use NLP
        structured = await rag_pipeline.parse_resume_structured(state["resume_text"])
        
        # Fallback if LLM extraction fails
        if "error" in structured:
            from app.services.ml_service import extract_experience_years
            exp = extract_experience_years(state["resume_text"])
            structured = {"experience": [{"duration": str(exp)}]}
            
        return {"parsed_resume": structured}

    # 2. Skill Extraction Agent
    async def skill_node(state: AgentState) -> dict:
        # Utilize the RAG parsed data, or fallback NER text
        from app.ml.llm_service import ai_llm_service
        skills = await ai_llm_service.extract_skills(state["resume_text"])
        return {"extracted_skills": skills}

    # 3. Matcher Agent
    async def matcher_node(state: AgentState) -> dict:
        from app.services.ml_service import advanced_ats_score
        
        clean_text = state["resume_text"]
        
        # This ties into the existing robust ATS logic for now,
        # augmented with the extracted state.
        result = advanced_ats_score(clean_text, state["job_role"])
        
        return {
            "ml_score": result["ml_score"],
            "skill_similarity": result["skill_similarity"],
            "semantic_score": result["semantic_score"],
            "ats_score": result["ats_score"],
            "role_fit": result["role_fit"],
            "found_skills": result["found_skills"],
            "missing_skills": result["missing_skills"],
            "top_roles": result["top_roles"],
            "hire_prob": result.get("hire_prob", 0.0),
            "confidence": result.get("confidence", 0.0)
        }

    # 4. Explainable AI Agent (Decision node)
    async def explain_node(state: AgentState) -> dict:
        from app.ml.llm_service import ai_llm_service
        
        score = state.get("role_fit", 0.0)
        role = state.get("job_role", "Unknown")
        found = state.get("found_skills", [])
        missing = state.get("missing_skills", [])
        
        prompt = f"""
        Provide a brief, concise hiring recommendation based on these scores:
        Role: {role}
        Overall Fit: {score}%
        Found Skills: {", ".join(found[:10])}
        Missing Skills: {", ".join(missing[:5])}
        
        If score > 75, recommend HIRE. If 50-75, recommend REVIEW. If < 50, recommend REJECT.
        Format your reasoning concisely.
        """
        
        reasoning = await ai_llm_service.generate_response(prompt)
        decision = "HIRE" if score > 75 else "REVIEW" if score > 50 else "REJECT"
        
        exp = {
            "selected_reasons": ["High semantic match"] if score > 70 else [],
            "rejected_reasons": ["Missing core skills"] if score < 50 else [],
            "matched_skills": found,
            "missing_skills": missing,
            "ai_reasoning": reasoning
        }
        
        return {"decision": decision, "explanation": exp}

    # Define Graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("parser", parser_node)
    workflow.add_node("skills", skill_node)
    workflow.add_node("matcher", matcher_node)
    workflow.add_node("explainer", explain_node)
    
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "skills")
    workflow.add_edge("skills", "matcher")
    workflow.add_edge("matcher", "explainer")
    workflow.add_edge("explainer", END)
    
    return workflow.compile()


coordinator_app = get_coordinator_app()

async def run_coordinator_pipeline(resume_text: str, job_role: str, job_profile: dict) -> dict:
    """Entry point for the Multi-Agent RAG pipeline."""
    if coordinator_app is None:
        # Fallback to legacy procedural logic if LangGraph is missing
        from app.services.ml_service import analyze_resume
        return analyze_resume(resume_text, job_role)
        
    initial_state = {
        "resume_text": resume_text,
        "job_role": job_role,
        "job_profile": job_profile
    }
    
    try:
        final_state = await coordinator_app.ainvoke(initial_state)
        return final_state
    except Exception as e:
        from app.core.logging_config import get_logger
        get_logger(__name__).error(f"Coordinator pipeline failed: {e}")
        # Fallback
        from app.services.ml_service import analyze_resume
        return analyze_resume(resume_text, job_role)
