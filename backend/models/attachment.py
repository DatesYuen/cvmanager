from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.database import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)  # paper, project, patent, etc.
    entity_id = Column(Integer, nullable=False)
    folder_id = Column(Integer, ForeignKey("attachment_folders.id"), nullable=True)
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(300), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
