from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Person, User
from backend.schemas.person import PersonCreate, PersonUpdate, PersonOut
from backend.services.auth_service import get_current_user, has_permission

router = APIRouter(prefix="/api/persons", tags=["persons"])


@router.get("/", response_model=List[PersonOut])
def list_persons(search: Optional[str] = None,
                 db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    q = db.query(Person)
    if search:
        q = q.filter((Person.name.contains(search)) | (Person.name_en.contains(search)))
    return q.order_by(Person.updated_at.desc()).all()


@router.post("/", response_model=PersonOut)
def create_person(data: PersonCreate,
                  db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    if not has_permission(user, "can_create_person"):
        raise HTTPException(status_code=403, detail="No permission to create person")
    person = Person(name=data.name, name_en=data.name_en, created_by=user.id)
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.get("/{person_id}", response_model=PersonOut)
def get_person(person_id: int, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    person = db.query(Person).get(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.put("/{person_id}", response_model=PersonOut)
def update_person(person_id: int, data: PersonUpdate,
                  db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    if not has_permission(user, "can_edit_person"):
        raise HTTPException(status_code=403, detail="No permission")
    person = db.query(Person).get(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(person, field, value)
    db.commit()
    db.refresh(person)
    return person


@router.delete("/{person_id}")
def delete_person(person_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    if not has_permission(user, "can_delete_person"):
        raise HTTPException(status_code=403, detail="No permission")
    person = db.query(Person).get(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    db.delete(person)
    db.commit()
    return {"msg": "Person deleted"}
