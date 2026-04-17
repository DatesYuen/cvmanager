from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class SoftwareCopyright(Base):
    __tablename__ = "software_copyrights"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    applicant = Column(String(500), default="")
    name = Column(String(500), default="")
    registration_date = Column(String(50), default="")
    registration_number = Column(String(100), default="")
    raw_text = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    review_status = Column(String(20), default="pending")

    person = relationship("Person", back_populates="software_copyrights")
