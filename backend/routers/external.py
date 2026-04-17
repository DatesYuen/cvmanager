"""External data enrichment placeholders."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.external import paper_api, patent_api
from backend.models import User
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/api/external", tags=["external"])


class PaperLookupRequest(BaseModel):
    doi: Optional[str] = None
    title: Optional[str] = None
    query: Optional[str] = None


class PatentLookupRequest(BaseModel):
    application_number: Optional[str] = None
    title: Optional[str] = None
    query: Optional[str] = None


class ExternalLookupResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = {}


@router.post("/paper-lookup", response_model=ExternalLookupResponse)
def lookup_paper(req: PaperLookupRequest, user: User = Depends(get_current_user)):
    if req.doi:
        return ExternalLookupResponse(**paper_api.lookup_by_doi(req.doi))
    if req.title:
        return ExternalLookupResponse(**paper_api.search_by_title(req.title))
    query = req.query or ""
    return ExternalLookupResponse(**paper_api.lookup(query))


@router.post("/patent-lookup", response_model=ExternalLookupResponse)
def lookup_patent(req: PatentLookupRequest, user: User = Depends(get_current_user)):
    query = req.application_number or req.title or req.query or ""
    return ExternalLookupResponse(**patent_api.lookup(query))
