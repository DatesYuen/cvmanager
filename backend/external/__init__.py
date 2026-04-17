"""External API placeholders for data enrichment."""
from typing import Optional, Dict, Any


class BaseExternalAPI:
    """Base class for external API integrations."""

    def lookup(self, query: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement lookup()")


class PaperLookupAPI(BaseExternalAPI):
    """Placeholder for paper information lookup (CrossRef, CNKI, etc.)."""

    def lookup(self, query: str, **kwargs) -> Dict[str, Any]:
        # TODO: Integrate with CrossRef API: https://api.crossref.org/works
        # TODO: Integrate with CNKI API for Chinese papers
        return {
            "success": False,
            "message": "Paper lookup API not configured. Integrate CrossRef or CNKI API.",
            "data": {}
        }

    def lookup_by_doi(self, doi: str) -> Dict[str, Any]:
        # TODO: GET https://api.crossref.org/works/{doi}
        return {"success": False, "message": "DOI lookup not configured", "data": {}}

    def search_by_title(self, title: str) -> Dict[str, Any]:
        # TODO: GET https://api.crossref.org/works?query.title={title}
        return {"success": False, "message": "Title search not configured", "data": {}}


class PatentLookupAPI(BaseExternalAPI):
    """Placeholder for patent information lookup."""

    def lookup(self, query: str, **kwargs) -> Dict[str, Any]:
        # TODO: Integrate with patent APIs (CNIPA, Google Patents, etc.)
        return {
            "success": False,
            "message": "Patent lookup API not configured.",
            "data": {}
        }


paper_api = PaperLookupAPI()
patent_api = PatentLookupAPI()
