from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .question_parser import (
    JUDGMENT_FALSE,
    JUDGMENT_TRUE,
    RawQuestion,
    infer_question_type,
    normalize_answer_tokens,
)

ISSUE_MISSING_QUESTION = "missing_question"
ISSUE_MISSING_OPTIONS = "missing_options"
ISSUE_MISSING_ANSWER = "missing_answer"
ISSUE_ANSWER_NOT_IN_OPTIONS = "answer_not_in_options"
ISSUE_UNKNOWN_TYPE = "unknown_type"
ISSUE_DUPLICATE_CANDIDATE = "duplicate_candidate"
ISSUE_MERGED_QUESTIONS = "merged_questions"


@dataclass
class ValidatedQuestion:
    chapter: Optional[str]
    question_type: str
    stem: str
    options: list[dict]
    answer: Optional[list[str]]
    explanation: Optional[str]
    source_order: int
    needs_review: bool
    issues: list[str] = field(default_factory=list)
    content_hash: Optional[str] = None
    duplicate_of: Optional[int] = None


def validate_question(raw: RawQuestion) -> ValidatedQuestion:
    issues: list[str] = []
    stem = raw.stem.strip()
    if not stem:
        issues.append(ISSUE_MISSING_QUESTION)

    if raw.merged_flag:
        issues.append(ISSUE_MERGED_QUESTIONS)

    answer: Optional[list[str]] = None
    if raw.answer_raw is None or not str(raw.answer_raw).strip():
        issues.append(ISSUE_MISSING_ANSWER)
        answer = None
    else:
        answer = normalize_answer_tokens(raw.answer_raw)
        if not answer:
            issues.append(ISSUE_MISSING_ANSWER)
            answer = None

    options = [
        {"label": o.label, "content": o.content, "sort_order": i}
        for i, o in enumerate(raw.options)
    ]

    qtype = infer_question_type(raw.options, answer)

    # 判断题可无显式选项
    if qtype == "judgment":
        if not options:
            options = [
                {"label": "对", "content": "对", "sort_order": 0},
                {"label": "错", "content": "错", "sort_order": 1},
            ]
    elif qtype in {"single_choice", "multiple_choice"}:
        if len(options) < 2:
            issues.append(ISSUE_MISSING_OPTIONS)
    else:
        if len(options) < 2 and answer is not None:
            # 有答案但无足够选项
            if not any(a in {"对", "错"} or a in JUDGMENT_TRUE or a in JUDGMENT_FALSE for a in (answer or [])):
                issues.append(ISSUE_MISSING_OPTIONS)
        if qtype == "unknown":
            issues.append(ISSUE_UNKNOWN_TYPE)

    if answer and options:
        labels = {o["label"].upper() for o in options}
        # 判断题答案映射
        normalized_answer = []
        for a in answer:
            if a in JUDGMENT_TRUE:
                normalized_answer.append("对" if "对" in labels or "对" in {o["content"] for o in options} else a)
            elif a in JUDGMENT_FALSE:
                normalized_answer.append("错" if "错" in labels or "错" in {o["content"] for o in options} else a)
            else:
                normalized_answer.append(a)
        answer = normalized_answer
        option_labels = {o["label"].upper() for o in options}
        # 也允许判断题用 A/B
        for a in answer:
            au = a.upper()
            if au not in option_labels and a not in option_labels:
                # 判断题特殊：答案为对/错且选项是 A/B 内容含对错
                if qtype == "judgment":
                    contents = " ".join(o["content"] for o in options)
                    if a in {"对", "错"} and (a in contents or "正确" in contents or "错误" in contents):
                        continue
                issues.append(ISSUE_ANSWER_NOT_IN_OPTIONS)
                break

    needs_review = bool(issues) or answer is None
    if answer is None:
        needs_review = True

    if qtype == "unknown":
        needs_review = True

    return ValidatedQuestion(
        chapter=raw.chapter,
        question_type=qtype if qtype != "unknown" or not options else (
            "multiple_choice" if answer and len(answer) > 1 else "single_choice" if options else "unknown"
        ),
        stem=stem or "(空题干)",
        options=options,
        answer=answer,
        explanation=raw.explanation,
        source_order=raw.source_order,
        needs_review=needs_review,
        issues=sorted(set(issues)),
    )


def validate_questions(raws: list[RawQuestion]) -> list[ValidatedQuestion]:
    return [validate_question(r) for r in raws]
