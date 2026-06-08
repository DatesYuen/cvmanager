from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    title = Column(String(500), default="")
    journal = Column(String(300), default="")
    year = Column(String(20), default="")
    doi = Column(String(300), default="")
    issue = Column(String(50), default="")
    volume = Column(String(50), default="")
    pages = Column(String(50), default="")
    cas_partition = Column(String(20), default="未收录")
    is_top_journal = Column(Boolean, default=False)
    issn = Column(String(50), default="")
    eissn = Column(String(50), default="")
    impact_factor = Column(Float, nullable=True)
    source_type = Column(String(20), default="未知")
    citation_count = Column(Integer, nullable=True)
    citation_note = Column(String(300), default="")
    is_first_author = Column(Boolean, default=False)
    is_corresponding_author = Column(Boolean, default=False)
    raw_text = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    review_status = Column(String(20), default="pending")  # pending/approved/rejected

    person = relationship("Person", back_populates="papers")
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan",
                           order_by="PaperAuthor.order")


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    name = Column(String(100), nullable=False)
    order = Column(Integer, default=0)
    is_first_author = Column(Boolean, default=False)
    is_corresponding_author = Column(Boolean, default=False)

    paper = relationship("Paper", back_populates="authors")
