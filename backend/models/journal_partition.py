from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from backend.database import Base


class JournalPartition(Base):
    __tablename__ = "journal_partitions"

    id = Column(Integer, primary_key=True, index=True)
    journal_name = Column(String(300), nullable=False, index=True)
    normalized_name = Column(String(300), nullable=False, unique=True, index=True)
    cas_partition = Column(String(20), default="未收录", index=True)
    cas_partition_code = Column(Integer, nullable=True, index=True)
    is_top = Column(Boolean, default=False, index=True)
    open_access = Column(Boolean, default=False)
    issn = Column(String(50), default="")
    eissn = Column(String(50), default="")
    category = Column(Text, default="")
    impact_factor = Column(Float, nullable=True)
    source_type = Column(String(20), default="未知")
    imported_from = Column(String(500), default="")
    imported_at = Column(DateTime, default=datetime.utcnow)
