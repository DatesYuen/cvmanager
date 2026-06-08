from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from backend.database import Base


class AttachmentFolder(Base):
    __tablename__ = "attachment_folders"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("attachment_folders.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
