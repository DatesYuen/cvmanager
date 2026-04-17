from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.database import Base


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    action = Column(String(20), nullable=False)  # approve / reject
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(Text, default="")
    reviewed_at = Column(DateTime, default=datetime.utcnow)
