import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Resume, Person, User
from backend.schemas.person import ResumeOut
from backend.services.auth_service import get_current_user
from backend.config import RESUME_UPLOAD_DIR

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/upload/{person_id}", response_model=ResumeOut)
def upload_resume(person_id: int,
                  file: UploadFile = File(...),
                  db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    person = db.query(Person).get(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    # Determine version
    latest = db.query(Resume).filter(Resume.person_id == person_id)\
        .order_by(Resume.version.desc()).first()
    version = (latest.version + 1) if latest else 1

    # Save file
    filename = f"{person_id}_{version}_{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = RESUME_UPLOAD_DIR / filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    resume = Resume(
        person_id=person_id,
        file_path=str(file_path),
        original_filename=file.filename,
        version=version,
        uploaded_by=user.id,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Trigger parsing
    from backend.services.resume_service import parse_resume
    parse_resume(db, resume, person)

    return resume


@router.get("/{person_id}/history", response_model=List[ResumeOut])
def resume_history(person_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return db.query(Resume).filter(Resume.person_id == person_id)\
        .order_by(Resume.version.desc()).all()


@router.get("/download/{resume_id}")
def download_resume(resume_id: int, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    resume = db.query(Resume).get(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(
        resume.file_path,
        filename=resume.original_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
