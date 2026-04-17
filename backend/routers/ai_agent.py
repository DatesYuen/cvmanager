"""AI Agent interfaces - placeholder for future AI integration."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas.ai import (
    AISettingsOut, AIReviewConfigOut, AIReviewRequest, AIReviewResponse, AISettingsBase,
    AISingleReviewRequest, AITestRequest, AITestResponse,
)
from backend.services.ai_review_service import (
    get_or_create_ai_settings,
    get_public_ai_review_config,
    ai_review_low_confidence_items,
    DEFAULT_AI_PROMPT_TEMPLATE,
    ai_review_single_item,
    test_ai_connection,
)
from backend.services.auth_service import get_current_user, require_admin, has_permission

router = APIRouter(prefix="/api/ai", tags=["ai-agent"])


class AIExtractRequest(BaseModel):
    raw_text: str
    entity_type: str
    context: Optional[str] = ""


class AIExtractResponse(BaseModel):
    success: bool
    fields: Dict[str, Any] = {}
    confidence: float = 0.0
    message: str = ""


class AIAnalyzeRequest(BaseModel):
    person_id: int
    analysis_type: str = "summary"  # summary, comparison, completeness


class AIAnalyzeResponse(BaseModel):
    success: bool
    result: Dict[str, Any] = {}
    message: str = ""


class AIFillFormRequest(BaseModel):
    person_id: int
    form_template: Dict[str, Any]
    entity_types: List[str] = []


class AIFillFormResponse(BaseModel):
    success: bool
    filled_form: Dict[str, Any] = {}
    message: str = ""


@router.get("/settings", response_model=AISettingsOut)
def get_ai_settings(db: Session = Depends(get_db), _=Depends(require_admin)):
    return get_or_create_ai_settings(db)


@router.put("/settings", response_model=AISettingsOut)
def update_ai_settings(data: AISettingsBase, db: Session = Depends(get_db), _=Depends(require_admin)):
    settings = get_or_create_ai_settings(db)
    payload = data.model_dump()
    if not payload.get("prompt_template"):
        payload["prompt_template"] = DEFAULT_AI_PROMPT_TEMPLATE
    for field, value in payload.items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/review-config", response_model=AIReviewConfigOut)
def get_ai_review_config(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not has_permission(user, "can_review"):
        raise HTTPException(status_code=403, detail="Review permission required")
    return AIReviewConfigOut(**get_public_ai_review_config(db))


@router.post("/review-low-confidence", response_model=AIReviewResponse)
def review_low_confidence(req: AIReviewRequest, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    if not has_permission(user, "can_review"):
        raise HTTPException(status_code=403, detail="Review permission required")
    result = ai_review_low_confidence_items(
        db=db,
        person_id=req.person_id,
        threshold=req.confidence_threshold,
        entity_types=req.entity_types,
        reviewer_id=user.id,
    )
    return AIReviewResponse(**result)


@router.post("/review-item", response_model=AIReviewResponse)
def review_single_item(req: AISingleReviewRequest, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    if not has_permission(user, "can_review"):
        raise HTTPException(status_code=403, detail="Review permission required")
    result = ai_review_single_item(db, req.entity_type, req.entity_id, reviewer_id=user.id)
    return AIReviewResponse(**result)


@router.post("/test", response_model=AITestResponse)
def test_ai(req: AITestRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    result = test_ai_connection(db, req.sample_text, req.entity_type)
    return AITestResponse(**result)


@router.post("/extract", response_model=AIExtractResponse)
def ai_extract(req: AIExtractRequest, user: User = Depends(get_current_user)):
    """AI-powered extraction for low-confidence items. TODO: Integrate AI service."""
    return AIExtractResponse(
        success=False,
        message="AI extraction service not yet configured. Please configure an AI provider."
    )


@router.post("/analyze", response_model=AIAnalyzeResponse)
def ai_analyze(req: AIAnalyzeRequest, user: User = Depends(get_current_user)):
    """AI-powered resume analysis. TODO: Integrate AI service."""
    return AIAnalyzeResponse(
        success=False,
        message="AI analysis service not yet configured."
    )


@router.post("/fill-form", response_model=AIFillFormResponse)
def ai_fill_form(req: AIFillFormRequest, user: User = Depends(get_current_user)):
    """AI-powered form filling. TODO: Integrate AI service."""
    return AIFillFormResponse(
        success=False,
        message="AI form filling service not yet configured."
    )
