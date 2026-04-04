"""
LangChain chain definitions for all AI features.
Uses LCEL (LangChain Expression Language) for composable pipelines.

Quota handling strategy:
- Try primary provider (Gemini by default)
- If 429 / RESOURCE_EXHAUSTED → mark router quota flag → immediately try Groq (llama-3.3-70b-versatile)
- No retries — one attempt per provider, fail fast and fall through
"""
import logging
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.ai.model_router import model_router, is_quota_error
from backend.ai.prompts import (
    RESUME_GENERATION_PROMPT, RESUME_ANALYSIS_PROMPT, COVER_LETTER_PROMPT,
    RECRUITER_SIM_PROMPT, INTERVIEW_QUESTION_PROMPT, INTERVIEW_EVAL_PROMPT,
    SKILL_GAP_PROMPT, EMAIL_GENERATION_PROMPT, GITHUB_ANALYSIS_PROMPT, JD_EXTRACTION_PROMPT,
)
from backend.utils.helpers import clean_ai_response, safe_json_parse

logger = logging.getLogger(__name__)


def _invoke(
    prompt_template: str,
    inputs: dict,
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
) -> str:
    """
    Core invoke function — single attempt with clean Groq fallback on quota error.

    Flow:
      1. Try primary provider (e.g. Gemini)
      2. If quota error → mark exhausted on router → try Groq once
      3. Any other error → raise immediately (no silent swallowing)

    Returns cleaned raw string from the LLM.
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)

    # Primary attempt
    try:
        llm, used_provider = model_router.get_llm_with_fallback(
            provider=provider, temperature=temperature, max_tokens=max_tokens
        )
        chain = prompt | llm | StrOutputParser()
        raw = chain.invoke(inputs)
        logger.info(f"LLM call succeeded via {used_provider}. Response length: {len(raw)}")
        return clean_ai_response(raw)

    except Exception as primary_err:
        if is_quota_error(primary_err):
            # Gemini quota hit — mark it and fall through to Groq
            logger.warning(f"Gemini quota/rate-limit error: {primary_err}")
            model_router.mark_gemini_quota_exhausted()
        else:
            # Non-quota error (bad request, network, etc.) — don't hide it
            logger.error(f"Primary LLM call failed (non-quota): {primary_err}")
            raise

    # Groq fallback — only reached after a quota error
    logger.info("Falling back to Groq (llama-3.3-70b-versatile) after Gemini quota exhaustion...")
    try:
        from backend.config import settings
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "Gemini API key is expired or exhausted, and Groq fallback is unavailable "
                "because GROQ_API_KEY is not set. Please update your AI API keys."
            )
            
        groq_llm = model_router.get_llm(provider="groq", temperature=temperature, max_tokens=max_tokens)
        chain = prompt | groq_llm | StrOutputParser()
        raw = chain.invoke(inputs)
        logger.info(f"Groq fallback succeeded. Response length: {len(raw)}")
        return clean_ai_response(raw)
    except Exception as groq_err:
        logger.error(f"Groq fallback also failed: {groq_err}")
        raise RuntimeError(
            f"Both primary provider and Groq fallback failed. "
            f"Groq error: {groq_err}"
        )


def _invoke_json(
    prompt_template: str,
    inputs: dict,
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
) -> dict:
    """
    Invoke and parse JSON. No retries — one clean attempt.
    Returns parsed dict or {"error": "..."} on failure.
    """
    try:
        raw = _invoke(prompt_template, inputs, provider=provider,
                      temperature=temperature, max_tokens=max_tokens)
        parsed = safe_json_parse(raw)
        if parsed and "error" not in parsed:
            return parsed
        logger.error(f"JSON parse failed. Raw preview: {raw[:300]}")
        return {"error": "Failed to parse AI response as JSON", "raw_preview": raw[:200]}

    except Exception as e:
        logger.error(f"_invoke_json failed: {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────
# Public chain functions
# ─────────────────────────────────────────────

def generate_resume(
    job_description: str,
    existing_resume: str = "",
    additional_context: str = "",
    provider: Optional[str] = None,
) -> dict:
    return _invoke_json(
        RESUME_GENERATION_PROMPT,
        {
            "job_description": job_description,
            "existing_resume": existing_resume or "Not provided - generate from job description",
            "additional_context": additional_context or "None",
        },
        provider=provider, temperature=0.6, max_tokens=8192,
    )


def analyze_resume(
    resume_text: str,
    job_description: str = "",
    provider: Optional[str] = None,
) -> dict:
    return _invoke_json(
        RESUME_ANALYSIS_PROMPT,
        {
            "resume_text": resume_text,
            "job_description": job_description or "No specific job description — do a general analysis",
        },
        provider=provider, temperature=0.2, max_tokens=4096,
    )


def generate_cover_letter(
    company_name: str,
    role: str,
    job_description: str = "",
    key_skills: str = "",
    tone: str = "formal",
    additional_context: str = "",
    user_profile: str = "",
    provider: Optional[str] = None,
) -> str:
    """Returns plain text (not JSON)."""
    return _invoke(
        COVER_LETTER_PROMPT,
        {
            "company_name": company_name, "role": role,
            "job_description": job_description or "Not provided",
            "key_skills": key_skills or "Not specified",
            "tone": tone,
            "additional_context": additional_context or "None",
            "user_profile": user_profile or "Not provided",
        },
        provider=provider, temperature=0.7, max_tokens=2048,
    )


def simulate_recruiter(
    resume_text: str,
    job_description: str,
    provider: Optional[str] = None,
) -> dict:
    return _invoke_json(
        RECRUITER_SIM_PROMPT,
        {"resume_text": resume_text, "job_description": job_description},
        provider=provider, temperature=0.4, max_tokens=4096,
    )


def generate_interview_questions(
    role: str,
    company: str = "",
    interview_type: str = "mixed",
    difficulty: str = "medium",
    num_questions: int = 5,
    provider: Optional[str] = None,
) -> dict:
    return _invoke_json(
        INTERVIEW_QUESTION_PROMPT,
        {
            "role": role, "company": company or "a tech company",
            "interview_type": interview_type, "difficulty": difficulty,
            "num_questions": str(num_questions),
        },
        provider=provider, temperature=0.7, max_tokens=4096,
    )


def evaluate_interview_answer(
    question: str,
    answer: str,
    role: str,
    provider: Optional[str] = None,
) -> dict:
    return _invoke_json(
        INTERVIEW_EVAL_PROMPT,
        {"question": question, "answer": answer, "role": role},
        provider=provider, temperature=0.3, max_tokens=2048,
    )


def analyze_skill_gap(
    job_description: str,
    user_skills: str = "",
    provider: Optional[str] = None,
) -> dict:
    return _invoke_json(
        SKILL_GAP_PROMPT,
        {"job_description": job_description, "user_skills": user_skills or "Not provided"},
        provider=provider, temperature=0.5, max_tokens=4096,
    )


def generate_email(
    email_type: str,
    recipient_name: str = "",
    company: str = "",
    role: str = "",
    context: str = "",
    tone: str = "professional",
    provider: Optional[str] = None,
) -> dict:
    return _invoke_json(
        EMAIL_GENERATION_PROMPT,
        {
            "email_type": email_type,
            "recipient_name": recipient_name or "Hiring Manager",
            "company": company or "the company",
            "role": role or "the position",
            "context": context or "None", "tone": tone,
        },
        provider=provider, temperature=0.7, max_tokens=1024,
    )


def analyze_github_repos(repos_data: str, provider: Optional[str] = None) -> dict:
    return _invoke_json(
        GITHUB_ANALYSIS_PROMPT,
        {"repos_data": repos_data},
        provider=provider, temperature=0.6, max_tokens=4096,
    )


def extract_jd_info(jd_text: str, provider: Optional[str] = None) -> dict:
    return _invoke_json(
        JD_EXTRACTION_PROMPT,
        {"jd_text": jd_text},
        provider=provider, temperature=0.2, max_tokens=2048,
    )
