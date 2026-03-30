"""Resume generation and management API routes."""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.schemas.resume import ResumeGenerateRequest, ResumeGenerateResponse, ResumeListItem
from backend.utils.auth import get_current_user
from backend.services.resume_service import resume_service
from backend.services.file_service import file_service

router = APIRouter(prefix="/api/resume", tags=["Resume"])


@router.post("/generate", response_model=ResumeGenerateResponse)
def generate_resume(req: ResumeGenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        context_str = req.existing_resume or ""
        if req.resume_data:
            context_str += "\n\nUser Data Input:\n" + req.resume_data.model_dump_json()
            
        resume = resume_service.generate(
            db=db,
            user_id=current_user.id,
            job_description=req.job_description or "No specific JD provided, create a general-purpose professional resume based on user data.",
            existing_resume=context_str,
            template_id=req.template_id,
            additional_context=req.additional_context or "",
        )
        content = json.loads(resume.content) if isinstance(resume.content, str) else resume.content
        return ResumeGenerateResponse(
            id=resume.id,
            title=resume.title,
            content=content,
            raw_text=resume.raw_text or "",
            ats_score=resume.ats_score,
            keywords_matched=json.loads(resume.keywords_matched) if resume.keywords_matched else [],
            keywords_missing=json.loads(resume.keywords_missing) if resume.keywords_missing else [],
            version=resume.version,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")


@router.get("/list", response_model=list[ResumeListItem])
def list_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resumes = resume_service.list_user_resumes(db, current_user.id)
    return [
        ResumeListItem(id=r.id, title=r.title, ats_score=r.ats_score, version=r.version, created_at=r.created_at)
        for r in resumes
    ]


@router.get("/{resume_id}")
def get_resume(resume_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = resume_service.get_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {
        "id": resume.id,
        "title": resume.title,
        "content": json.loads(resume.content) if isinstance(resume.content, str) else resume.content,
        "raw_text": resume.raw_text,
        "ats_score": resume.ats_score,
        "version": resume.version,
        "created_at": resume.created_at,
    }


@router.get("/{resume_id}/versions")
def get_versions(resume_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    versions = resume_service.get_versions(db, resume_id)
    return [
        {
            "id": v.id,
            "version_number": v.version_number,
            "change_summary": v.change_summary,
            "ats_score": v.ats_score,
            "created_at": v.created_at,
        }
        for v in versions
    ]


@router.post("/{resume_id}/download/{format}")
def download_resume(resume_id: int, format: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = resume_service.get_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    content = json.loads(resume.content) if isinstance(resume.content, str) else resume.content

    if format == "pdf":
        html = file_service.render_template("resume_reference.html", content)
        filepath = file_service.generate_pdf(html)
    elif format == "docx":
        filepath = file_service.generate_docx(content)
    elif format == "txt":
        filepath = file_service.generate_txt(content)
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use: pdf, docx, txt")

    if not filepath:
        raise HTTPException(status_code=500, detail="File generation failed")

    return FileResponse(filepath, filename=f"resume.{format}", media_type="application/octet-stream")


@router.delete("/{resume_id}")
def delete_resume(resume_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if resume_service.delete(db, resume_id, current_user.id):
        return {"message": "Resume deleted"}
    raise HTTPException(status_code=404, detail="Resume not found")
