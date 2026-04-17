"""Diff engine: compare old and new resume data to detect changes."""
from difflib import SequenceMatcher
from typing import List, Dict, Any, Tuple


SIMILARITY_THRESHOLD = 0.75


def compute_text_similarity(a: str, b: str) -> float:
    """Compute similarity ratio between two text strings."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.strip(), b.strip()).ratio()


def diff_items(old_items: List[Dict[str, Any]],
               new_items: List[Dict[str, Any]],
               key_field: str = "raw_text") -> Dict[str, List]:
    """Compare old and new items, categorizing into added, modified, unchanged.

    Returns:
        {
            "added": [new items not matching any old item],
            "modified": [(old_item, new_item) pairs with changes],
            "unchanged": [items that match closely],
            "removed": [old items not matching any new item],
        }
    """
    result = {"added": [], "modified": [], "unchanged": [], "removed": []}

    # Build similarity matrix
    matched_old = set()
    matched_new = set()

    matches = []
    for i, new_item in enumerate(new_items):
        best_score = 0
        best_j = -1
        for j, old_item in enumerate(old_items):
            if j in matched_old:
                continue
            score = compute_text_similarity(
                str(new_item.get(key_field, "")),
                str(old_item.get(key_field, ""))
            )
            if score > best_score:
                best_score = score
                best_j = j
        if best_score >= SIMILARITY_THRESHOLD and best_j >= 0:
            matches.append((i, best_j, best_score))

    # Sort by score descending to get best matches first
    matches.sort(key=lambda x: x[2], reverse=True)

    for new_idx, old_idx, score in matches:
        if new_idx in matched_new or old_idx in matched_old:
            continue
        matched_new.add(new_idx)
        matched_old.add(old_idx)

        if score >= 0.98:
            result["unchanged"].append(new_items[new_idx])
        else:
            result["modified"].append((old_items[old_idx], new_items[new_idx]))

    # Remaining unmatched items
    for i, item in enumerate(new_items):
        if i not in matched_new:
            result["added"].append(item)

    for j, item in enumerate(old_items):
        if j not in matched_old:
            result["removed"].append(item)

    return result
