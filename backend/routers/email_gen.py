"""Email generation API routes."""
from fastapi import APIRouter, Depends, HTTPException
from backend.utils.auth import get_current_user
from backend.schemas.ai import EmailGenerateRequest, EmailGenerateResponse
from backend.services.email_service import email_service

router = APIRouter(prefix="/api/email", tags=["Email"])


@router.post("/generate", response_model=EmailGenerateResponse)
def generate_email(req: EmailGenerateRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = email_service.generate(
            email_type=req.email_type,
            recipient=req.recipient_name or "",
            company=req.company or "",
            role=req.role or "",
            context=req.context or "",
            tone=req.tone,
        )
        return EmailGenerateResponse(
            subject=result.get("subject", ""),
            body=result.get("body", ""),
            email_type=req.email_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
