"""Mock interview API routes."""
from fastapi import APIRouter, Depends, HTTPException
from backend.schemas.ai import InterviewGenerateRequest, InterviewEvaluateRequest, InterviewResponse, InterviewEvaluation
from backend.utils.auth import get_current_user
from backend.services.interview_service import interview_service

router = APIRouter(prefix="/api/interview", tags=["Interview"])


@router.post("/generate", response_model=InterviewResponse)
def generate_questions(req: InterviewGenerateRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = interview_service.generate_questions(
            role=req.role, company=req.company or "",
            interview_type=req.interview_type, difficulty=req.difficulty,
            num_questions=req.num_questions,
        )
        questions = result.get("questions", []) if isinstance(result, dict) else []
        return InterviewResponse(questions=questions, role=req.role, interview_type=req.interview_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate", response_model=InterviewEvaluation)
def evaluate_answer(req: InterviewEvaluateRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = interview_service.evaluate_answer(req.question, req.answer, req.role)
        return InterviewEvaluation(
            score=result.get("score", 0),
            feedback=result.get("feedback", ""),
            strengths=result.get("strengths", []),
            improvements=result.get("improvements", []),
            sample_answer=result.get("sample_answer", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
