from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, ReviewRecord
from backend.schemas.common import (ReviewActionRequest, BatchReviewRequest, ReviewRecordOut)
from backend.services.auth_service import get_current_user
from backend.services.review_service import (
    apply_review_action, batch_approve_by_confidence, get_pending_items
)

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/pending/{person_id}")
def get_pending(person_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    return get_pending_items(db, person_id)


@router.post("/action")
def review_action(req: ReviewActionRequest, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    result = apply_review_action(db, req, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"msg": f"Action '{req.action}' applied"}


@router.post("/batch-action")
def batch_action(items: List[ReviewActionRequest], db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    for item in items:
        apply_review_action(db, item, user.id)
    return {"msg": f"{len(items)} items reviewed"}


@router.post("/batch-approve")
def batch_approve(req: BatchReviewRequest, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    count = batch_approve_by_confidence(db, req, user.id)
    return {"msg": f"{count} items approved"}


@router.get("/history/{person_id}", response_model=List[ReviewRecordOut])
def review_history(person_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return db.query(ReviewRecord).filter(ReviewRecord.person_id == person_id)\
        .order_by(ReviewRecord.reviewed_at.desc()).all()
