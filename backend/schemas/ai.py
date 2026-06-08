from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class AISettingsBase(BaseModel):
    response_api_url: str = "https://api.openai.com/v1/responses"
    api_key: str = ""
    model: str = "gpt-4.1-mini"
    prompt_template: str = ""
    ai_review_confidence_threshold: float = 0.6
    ai_review_concurrency: int = 2
    ai_review_retry_count: int = 1


class AISettingsOut(AISettingsBase):
    id: int
    provider_name: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIReviewConfigOut(BaseModel):
    configured: bool
    model: str
    ai_review_confidence_threshold: float
    ai_review_concurrency: int
    ai_review_retry_count: int


class AIReviewRequest(BaseModel):
    person_id: int
    confidence_threshold: Optional[float] = None
    entity_types: Optional[List[str]] = None


class AISingleReviewRequest(BaseModel):
    entity_type: str
    entity_id: int
    raw_text: Optional[str] = None


class AITestRequest(BaseModel):
    sample_text: str = "Shanchen Pang, Chuang Lin. A test paper title. Journal of Test, 2024."
    entity_type: str = "papers"


class AITestResponse(BaseModel):
    success: bool
    message: str = ""
    parsed_result: Dict[str, Any] = {}


class AIReviewResponse(BaseModel):
    success: bool
    total_count: int = 0
    reviewed_count: int = 0
    reviewed: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []
