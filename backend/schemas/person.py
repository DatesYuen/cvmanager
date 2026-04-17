from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class PersonBase(BaseModel):
    name: str
    name_en: str = ""


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None


class PersonOut(PersonBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeOut(BaseModel):
    id: int
    person_id: int
    original_filename: str
    version: int
    uploaded_by: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True
