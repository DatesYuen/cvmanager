"""Profile, education, and work experience endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Profile, Education, WorkExperience, User
from backend.schemas.items import (
    ProfileOut, ProfileUpdate,
    EducationOut, EducationCreate, EducationUpdate,
    WorkExperienceOut, WorkExperienceCreate, WorkExperienceUpdate,
)
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/{person_id}", response_model=ProfileOut)
def get_profile(person_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.person_id == person_id).first()
    if not profile:
        # Return empty profile
        return ProfileOut(id=0, person_id=person_id, introduction="", phone="", email="", address="")
    return profile


@router.put("/{person_id}", response_model=ProfileOut)
def update_profile(person_id: int, data: ProfileUpdate,
                   db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.person_id == person_id).first()
    if not profile:
        profile = Profile(person_id=person_id)
        db.add(profile)
        db.flush()
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{person_id}/educations", response_model=List[EducationOut])
def get_educations(person_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return db.query(Education).filter(Education.person_id == person_id).all()


@router.post("/{person_id}/educations", response_model=EducationOut)
def create_education(person_id: int, data: EducationCreate,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    education = Education(person_id=person_id, **data.model_dump(exclude={"person_id"}))
    db.add(education)
    db.commit()
    db.refresh(education)
    return education


@router.put("/educations/{education_id}", response_model=EducationOut)
def update_education(education_id: int, data: EducationUpdate,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    education = db.query(Education).get(education_id)
    if not education:
        raise HTTPException(status_code=404, detail="Education not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(education, field, value)
    db.commit()
    db.refresh(education)
    return education


@router.delete("/educations/{education_id}")
def delete_education(education_id: int, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    education = db.query(Education).get(education_id)
    if not education:
        raise HTTPException(status_code=404, detail="Education not found")
    db.delete(education)
    db.commit()
    return {"msg": "Education deleted"}


@router.get("/{person_id}/work-experiences", response_model=List[WorkExperienceOut])
def get_work_experiences(person_id: int, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    return db.query(WorkExperience).filter(WorkExperience.person_id == person_id).all()


@router.post("/{person_id}/work-experiences", response_model=WorkExperienceOut)
def create_work_experience(person_id: int, data: WorkExperienceCreate,
                           db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    work = WorkExperience(person_id=person_id, **data.model_dump(exclude={"person_id"}))
    db.add(work)
    db.commit()
    db.refresh(work)
    return work


@router.put("/work-experiences/{work_id}", response_model=WorkExperienceOut)
def update_work_experience(work_id: int, data: WorkExperienceUpdate,
                           db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    work = db.query(WorkExperience).get(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work experience not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(work, field, value)
    db.commit()
    db.refresh(work)
    return work


@router.delete("/work-experiences/{work_id}")
def delete_work_experience(work_id: int, db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    work = db.query(WorkExperience).get(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work experience not found")
    db.delete(work)
    db.commit()
    return {"msg": "Work experience deleted"}
