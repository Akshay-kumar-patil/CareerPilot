"""AI-related Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AIModelConfig(BaseModel):
    provider: str = "auto"  # openai, groq, auto
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class InterviewGenerateRequest(BaseModel):
    role: str
    company: Optional[str] = None
    interview_type: str = "mixed"  # hr, technical, mixed
    difficulty: str = "medium"  # easy, medium, hard
    num_questions: int = 5


class InterviewEvaluateRequest(BaseModel):
    question: str
    answer: str
    role: str


class InterviewResponse(BaseModel):
    questions: List[Dict[str, Any]]
    role: str
    interview_type: str


class InterviewEvaluation(BaseModel):
    score: float
    feedback: str
    strengths: List[str]
    improvements: List[str]
    sample_answer: str


class SkillGapRequest(BaseModel):
    job_description: str
    user_skills: Optional[List[str]] = None


class SkillGapResponse(BaseModel):
    missing_skills: List[Dict[str, Any]]
    matched_skills: List[str]
    skill_score: float
    learning_roadmap: List[Dict[str, Any]]
    suggested_projects: List[str]


class EmailGenerateRequest(BaseModel):
    email_type: str  # cold_email, referral_request, follow_up, thank_you
    recipient_name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    context: Optional[str] = None
    tone: str = "professional"


class EmailGenerateResponse(BaseModel):
    subject: str
    body: str
    email_type: str


class GitHubAnalyzeRequest(BaseModel):
    username: str
    max_repos: int = 10


class GitHubAnalyzeResponse(BaseModel):
    username: str
    repos: List[Dict[str, Any]]
    resume_points: List[str]
    tech_stack: List[str]


class RecruiterSimRequest(BaseModel):
    resume_text: str
    job_description: str


class RecruiterSimResponse(BaseModel):
    decision: str  # shortlisted, rejected
    confidence: float
    reasoning: List[str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


class ExtractionRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None


class ExtractionResponse(BaseModel):
    skills: List[str]
    responsibilities: List[str]
    requirements: List[str]
    tools: List[str]
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None


class AnalyticsSummary(BaseModel):
    total_applications: int
    applications_by_status: Dict[str, int]
    response_rate: float
    interview_rate: float
    offer_rate: float
    avg_excitement: float
    applications_this_month: int
    top_companies: List[Dict[str, Any]]
    application_trend: List[Dict[str, Any]]
    source_distribution: Dict[str, int]
    resume_performance: List[Dict[str, Any]]
