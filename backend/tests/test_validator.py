from app.services.duplicate_detector import mark_duplicates
from app.services.question_parser import RawOption, RawQuestion, parse_questions
from app.services.question_validator import (
    ISSUE_MISSING_ANSWER,
    validate_question,
    validate_questions,
)


def test_validate_standard(standard_docx):
    raws = parse_questions(standard_docx)
    validated = validate_questions(raws)
    assert len(validated) == 3
    types = {q.question_type for q in validated}
    assert "single_choice" in types or "judgment" in types
    multi = [q for q in validated if q.answer and len(q.answer) > 1]
    assert multi
    assert multi[0].question_type == "multiple_choice"
    assert all(isinstance(q.answer, list) for q in validated if q.answer is not None)


def test_missing_answer_needs_review(missing_answer_docx):
    raws = parse_questions(missing_answer_docx)
    validated = validate_questions(raws)
    assert validated
    assert any(ISSUE_MISSING_ANSWER in q.issues for q in validated)
    for q in validated:
        if ISSUE_MISSING_ANSWER in q.issues:
            assert q.answer is None
            assert q.needs_review is True


def test_answer_not_guessed():
    raw = RawQuestion(
        stem_parts=["没有答案的题"],
        options=[RawOption("A", "1"), RawOption("B", "2")],
        answer_raw=None,
        source_order=1,
    )
    v = validate_question(raw)
    assert v.answer is None
    assert v.needs_review
    assert ISSUE_MISSING_ANSWER in v.issues


def test_duplicate_candidate():
    raw = RawQuestion(
        stem_parts=["同一题干"],
        options=[RawOption("A", "1"), RawOption("B", "2")],
        answer_raw="A",
        source_order=1,
    )
    raw2 = RawQuestion(
        stem_parts=["同一题干"],
        options=[RawOption("A", "1"), RawOption("B", "2")],
        answer_raw="A",
        source_order=2,
    )
    validated = mark_duplicates(validate_questions([raw, raw2]))
    assert "duplicate_candidate" in validated[1].issues
