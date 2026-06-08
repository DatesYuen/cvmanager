"""Helpers for paper authors and person-name matching."""
import re
from typing import Iterable

from sqlalchemy.orm import Session

from backend.external import paper_api
from backend.services.journal_partition_service import apply_partition_to_paper_data


def normalize_person_name(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r'[\s,，.．·]+', ' ', value)
    return value.strip()


def build_person_aliases(name: str, name_en: str = "") -> set[str]:
    aliases = set()

    def add_alias(value: str):
        normalized = normalize_person_name(value)
        if normalized:
            aliases.add(normalized)
            aliases.add(normalized.replace(" ", ""))

    add_alias(name)
    add_alias(name_en)

    normalized_en = normalize_person_name(name_en)
    if normalized_en:
        parts = normalized_en.split()
        if len(parts) >= 2:
            add_alias(" ".join(reversed(parts)))

    return aliases


def author_matches_person(author_name: str, aliases: Iterable[str]) -> bool:
    normalized_author = normalize_person_name(author_name).replace("*", "").strip()
    compact_author = normalized_author.replace(" ", "")
    alias_set = set(aliases)
    return normalized_author in alias_set or compact_author in alias_set


def derive_paper_role_flags(authors: list[dict], person_name: str, person_name_en: str = "") -> dict:
    aliases = build_person_aliases(person_name, person_name_en)
    matching_author = None
    for author in authors:
        if author_matches_person(author.get("name", ""), aliases):
            matching_author = author
            break

    return {
        "is_first_author": bool(matching_author and matching_author.get("is_first_author")),
        "is_corresponding_author": bool(matching_author and matching_author.get("is_corresponding_author")),
    }


def enrich_paper_data(db: Session, paper_data: dict, fetch_external: bool = True) -> dict:
    """Fill paper metadata from public APIs and the local CAS/JCR partition table."""
    data = dict(paper_data)
    if fetch_external and _needs_external_lookup(data):
        metadata = _lookup_public_metadata(data)
        for field in ("title", "journal", "year", "doi", "volume", "issue", "pages"):
            if not data.get(field) and metadata.get(field):
                data[field] = str(metadata[field])
        for field in ("citation_count", "citation_note"):
            if data.get(field) in (None, "") and metadata.get(field) not in (None, ""):
                data[field] = metadata[field]

    apply_partition_to_paper_data(db, data)
    if not data.get("citation_note") and data.get("citation_count") is not None:
        data["citation_note"] = f"公开源未提供严格他引；总被引 {data['citation_count']}"
    return data


def _needs_external_lookup(data: dict) -> bool:
    if data.get("doi"):
        return True
    return any(not data.get(field) for field in ("title", "journal", "year", "volume", "issue", "pages"))


def _lookup_public_metadata(data: dict) -> dict:
    try:
        if data.get("doi"):
            result = paper_api.lookup_by_doi(data["doi"])
        elif data.get("title"):
            result = paper_api.search_by_title(data["title"])
        else:
            result = paper_api.lookup(data.get("raw_text", ""))
    except Exception:  # noqa: BLE001 - public API failures must not block resume ingestion.
        return {}
    if not result.get("success"):
        return {}
    return result.get("data") or {}
