from __future__ import annotations

import hashlib
import re
from typing import Optional

from .question_validator import ISSUE_DUPLICATE_CANDIDATE, ValidatedQuestion


def normalize_stem(stem: str) -> str:
    text = stem.strip().lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。、“”‘’？?！!：:；;（）()【】\[\]《》<>]", "", text)
    return text


def content_hash(stem: str, option_labels: list[str] | None = None) -> str:
    base = normalize_stem(stem)
    if option_labels:
        base += "|" + ",".join(sorted(option_labels))
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def attach_hashes(questions: list[ValidatedQuestion]) -> list[ValidatedQuestion]:
    for q in questions:
        labels = [o["label"] for o in q.options]
        q.content_hash = content_hash(q.stem, labels)
    return questions


def mark_duplicates(
    questions: list[ValidatedQuestion],
    existing_hashes: Optional[dict[str, int]] = None,
) -> list[ValidatedQuestion]:
    """标记重复候选：同批内重复 + 与已有题库重复."""
    existing_hashes = existing_hashes or {}
    seen: dict[str, int] = {}
    attach_hashes(questions)
    for idx, q in enumerate(questions):
        h = q.content_hash or ""
        if h in existing_hashes:
            q.issues = sorted(set(q.issues + [ISSUE_DUPLICATE_CANDIDATE]))
            q.duplicate_of = existing_hashes[h]
            q.needs_review = True
        elif h in seen:
            q.issues = sorted(set(q.issues + [ISSUE_DUPLICATE_CANDIDATE]))
            q.duplicate_of = seen[h]
            q.needs_review = True
        else:
            seen[h] = idx
    return questions
