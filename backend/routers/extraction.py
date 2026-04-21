"""JD/PDF extraction API routes."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.schemas.ai import ExtractionRequest
from backend.utils.auth import get_current_user
from backend.services.extraction_service import extraction_service
from backend.utils.pdf_parser import extract_text_from_file

router = APIRouter(prefix="/api/extract", tags=["Extraction"])


@router.post("/jd")
def extract_jd(req: ExtractionRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = extraction_service.parse_jd(text=req.text, url=req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file")
async def extract_from_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    text = extract_text_from_file(content, file.filename)
    return {"filename": file.filename, "text": text}


@router.post("/url")
def extract_from_url(req: ExtractionRequest, current_user: dict = Depends(get_current_user)):
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")
    text = extraction_service.extract_from_url(req.url)
    return {"url": req.url, "text": text}
