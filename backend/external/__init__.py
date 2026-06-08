"""External API integrations for paper and patent metadata enrichment."""
import json
import re
from typing import Dict, Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class BaseExternalAPI:
    """Base class for external API integrations."""

    def lookup(self, query: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement lookup()")


class PaperLookupAPI(BaseExternalAPI):
    """Lookup paper metadata from Semantic Scholar, OpenAlex, and Crossref."""

    def lookup(self, query: str, **kwargs) -> Dict[str, Any]:
        query = (query or "").strip()
        if not query:
            return {"success": False, "message": "Empty paper query", "data": {}}
        doi = _extract_doi(query)
        if doi:
            return self.lookup_by_doi(doi)
        return self.search_by_title(query)

    def lookup_by_doi(self, doi: str) -> Dict[str, Any]:
        doi = _clean_doi(doi)
        if not doi:
            return {"success": False, "message": "Empty DOI", "data": {}}

        lookups = [
            ("Semantic Scholar", self._semantic_by_doi),
            ("OpenAlex", self._openalex_by_doi),
            ("Crossref", self._crossref_by_doi),
        ]
        errors = []
        for source, func in lookups:
            data, message = func(doi)
            if data:
                data["metadata_source"] = source
                return {"success": True, "message": f"{source} matched by DOI", "data": data}
            if message:
                errors.append(f"{source}: {message}")
        return {"success": False, "message": "; ".join(errors) or "No paper metadata found", "data": {}}

    def search_by_title(self, title: str) -> Dict[str, Any]:
        title = (title or "").strip()
        if not title:
            return {"success": False, "message": "Empty title", "data": {}}

        lookups = [
            ("Semantic Scholar", self._semantic_by_title),
            ("OpenAlex", self._openalex_by_title),
            ("Crossref", self._crossref_by_title),
        ]
        errors = []
        for source, func in lookups:
            data, message = func(title)
            if data:
                data["metadata_source"] = source
                return {"success": True, "message": f"{source} matched by title", "data": data}
            if message:
                errors.append(f"{source}: {message}")
        return {"success": False, "message": "; ".join(errors) or "No paper metadata found", "data": {}}

    def _semantic_by_doi(self, doi: str):
        fields = "title,venue,publicationVenue,journal,year,citationCount,externalIds,publicationDate"
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{quote(doi, safe='')}?fields={fields}"
        payload, error = _get_json(url)
        if error or not payload:
            return None, error
        return _semantic_to_metadata(payload), ""

    def _semantic_by_title(self, title: str):
        params = urlencode({
            "query": title,
            "limit": 1,
            "fields": "title,venue,publicationVenue,journal,year,citationCount,externalIds,publicationDate",
        })
        payload, error = _get_json(f"https://api.semanticscholar.org/graph/v1/paper/search?{params}")
        if error or not payload.get("data"):
            return None, error
        return _semantic_to_metadata(payload["data"][0]), ""

    def _openalex_by_doi(self, doi: str):
        url = f"https://api.openalex.org/works/doi:{quote(doi, safe='')}"
        payload, error = _get_json(url)
        if error or not payload:
            return None, error
        return _openalex_to_metadata(payload), ""

    def _openalex_by_title(self, title: str):
        params = urlencode({"search": title, "per-page": 1})
        payload, error = _get_json(f"https://api.openalex.org/works?{params}")
        if error or not payload.get("results"):
            return None, error
        return _openalex_to_metadata(payload["results"][0]), ""

    def _crossref_by_doi(self, doi: str):
        payload, error = _get_json(f"https://api.crossref.org/works/{quote(doi, safe='')}")
        message = payload.get("message", {}) if payload else {}
        if error or not message:
            return None, error
        return _crossref_to_metadata(message), ""

    def _crossref_by_title(self, title: str):
        params = urlencode({"query.title": title, "rows": 1})
        payload, error = _get_json(f"https://api.crossref.org/works?{params}")
        items = payload.get("message", {}).get("items", []) if payload else []
        if error or not items:
            return None, error
        return _crossref_to_metadata(items[0]), ""


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


def _get_json(url: str, timeout: float = 5.0):
    headers = {"User-Agent": "cvmanager/1.0 (mailto:admin@example.com)"}
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")), ""
    except HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, str(exc)


def _clean_doi(value: str) -> str:
    doi = str(value or "").strip()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.I)
    return re.sub(r"[\s\]\)）.,，。；;]+$", "", doi)


def _extract_doi(value: str) -> str:
    match = re.search(r"10\.\d{4,9}/[^\s,，]+", value or "", re.I)
    return _clean_doi(match.group(0)) if match else ""


def _semantic_to_metadata(payload: dict) -> dict:
    journal = payload.get("journal") or {}
    publication_venue = payload.get("publicationVenue") or {}
    external_ids = payload.get("externalIds") or {}
    return _compact_metadata({
        "title": payload.get("title"),
        "journal": publication_venue.get("name") or journal.get("name") or payload.get("venue"),
        "year": str(payload.get("year") or ""),
        "volume": journal.get("volume"),
        "pages": journal.get("pages"),
        "doi": external_ids.get("DOI"),
        "citation_count": payload.get("citationCount"),
        "citation_note": _citation_note("Semantic Scholar", payload.get("citationCount")),
    })


def _openalex_to_metadata(payload: dict) -> dict:
    biblio = payload.get("biblio") or {}
    primary_location = payload.get("primary_location") or {}
    source = primary_location.get("source") or {}
    doi = str((payload.get("ids") or {}).get("doi") or payload.get("doi") or "")
    return _compact_metadata({
        "title": payload.get("display_name"),
        "journal": source.get("display_name"),
        "year": str(payload.get("publication_year") or ""),
        "volume": biblio.get("volume"),
        "issue": biblio.get("issue"),
        "pages": biblio.get("first_page") and biblio.get("last_page")
                 and f"{biblio.get('first_page')}-{biblio.get('last_page')}",
        "doi": _clean_doi(doi),
        "citation_count": payload.get("cited_by_count"),
        "citation_note": _citation_note("OpenAlex", payload.get("cited_by_count")),
    })


def _crossref_to_metadata(payload: dict) -> dict:
    title = _first(payload.get("title"))
    journal = _first(payload.get("container-title"))
    year = _year_from_crossref(payload)
    return _compact_metadata({
        "title": title,
        "journal": journal,
        "year": str(year or ""),
        "volume": payload.get("volume"),
        "issue": payload.get("issue"),
        "pages": payload.get("page"),
        "doi": _clean_doi(payload.get("DOI") or ""),
    })


def _first(value):
    if isinstance(value, list) and value:
        return value[0]
    return value


def _year_from_crossref(payload: dict):
    for key in ("published-print", "published-online", "published", "issued"):
        date_parts = (payload.get(key) or {}).get("date-parts")
        if date_parts and date_parts[0]:
            return date_parts[0][0]
    return None


def _citation_note(source: str, count) -> str:
    if count is None:
        return ""
    return f"公开源未提供严格他引；{source}总被引 {count}"


def _compact_metadata(data: dict) -> dict:
    return {key: value for key, value in data.items() if value not in (None, "")}
