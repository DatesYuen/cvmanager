from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class IndustryStandard(Base):
    __tablename__ = "industry_standards"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    name = Column(String(500), default="")
    publish_date = Column(String(50), default="")
    role = Column(String(100), default="")
    raw_text = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    review_status = Column(String(20), default="pending")

    person = relationship("Person", back_populates="industry_standards")
