"""GitHub analyzer API routes."""
from fastapi import APIRouter, Depends, HTTPException
from backend.schemas.ai import GitHubAnalyzeRequest, GitHubAnalyzeResponse
from backend.utils.auth import get_current_user
from backend.services.github_service import github_service

router = APIRouter(prefix="/api/github", tags=["GitHub"])


@router.post("/analyze")
def analyze_github(req: GitHubAnalyzeRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = github_service.analyze(req.username, req.max_repos)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
