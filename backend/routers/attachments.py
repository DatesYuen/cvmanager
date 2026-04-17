import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Attachment, User
from backend.schemas.common import AttachmentOut
from backend.services.auth_service import get_current_user
from backend.config import ATTACHMENT_UPLOAD_DIR

router = APIRouter(prefix="/api/attachments", tags=["attachments"])


@router.get("/", response_model=List[AttachmentOut])
def list_attachments(entity_type: str, entity_id: int,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    return db.query(Attachment).filter(
        Attachment.entity_type == entity_type,
        Attachment.entity_id == entity_id
    ).all()


@router.post("/upload", response_model=AttachmentOut)
def upload_attachment(entity_type: str, entity_id: int,
                      file: UploadFile = File(...),
                      db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    filename = f"{entity_type}_{entity_id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = ATTACHMENT_UPLOAD_DIR / filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    attachment = Attachment(
        entity_type=entity_type,
        entity_id=entity_id,
        file_path=str(file_path),
        original_filename=file.filename,
        uploaded_by=user.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/download/{attachment_id}")
def download_attachment(attachment_id: int, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    att = db.query(Attachment).get(attachment_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if not os.path.exists(att.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(att.file_path, filename=att.original_filename)


@router.delete("/{attachment_id}")
def delete_attachment(attachment_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    att = db.query(Attachment).get(attachment_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if os.path.exists(att.file_path):
        os.remove(att.file_path)
    db.delete(att)
    db.commit()
    return {"msg": "Attachment deleted"}
