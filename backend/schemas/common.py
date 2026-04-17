from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AttachmentOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    original_filename: str
    uploaded_by: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ReviewActionRequest(BaseModel):
    entity_type: str
    entity_id: int
    action: str  # approve / reject
    comment: str = ""
    updated_fields: Optional[Dict[str, Any]] = None


class BatchReviewRequest(BaseModel):
    person_id: int
    entity_types: Optional[List[str]] = None  # None = all
    confidence_threshold: float = 0.8
    action: str = "approve"


class ReviewRecordOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    person_id: int
    action: str
    reviewer_id: Optional[int] = None
    comment: str = ""
    reviewed_at: datetime

    class Config:
        from_attributes = True


class ExportFilterCondition(BaseModel):
    field: str
    op: str = "eq"  # eq, ne, contains, gt, lt, gte, lte, in
    value: object


class ExportRequest(BaseModel):
    entity_type: Optional[str] = None
    person_id: Optional[int] = None
    filters: List[ExportFilterCondition] = []
    fields: Optional[List[str]] = None  # selected columns
    format: str = "json"  # json / xlsx / docx
