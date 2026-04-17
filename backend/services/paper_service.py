"""Helpers for paper authors and person-name matching."""
import re
from typing import Iterable


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
