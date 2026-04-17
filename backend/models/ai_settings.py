from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime

from backend.database import Base


class AISettings(Base):
    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(50), default="openai")
    response_api_url = Column(String(500), default="https://api.openai.com/v1/responses")
    api_key = Column(Text, default="")
    model = Column(String(100), default="gpt-4.1-mini")
    prompt_template = Column(Text, default="")
    ai_review_confidence_threshold = Column(Float, default=0.6)
    ai_review_concurrency = Column(Integer, default=2)
    ai_review_retry_count = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
