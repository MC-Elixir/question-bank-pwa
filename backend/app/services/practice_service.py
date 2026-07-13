from __future__ import annotations

import random
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from ..database.models import AnswerRecord, Question, QuestionProgress


def list_questions(
    db: Session,
    bank_id: int,
    mode: str = "sequence",
) -> list[Question]:
    query = (
        db.query(Question)
        .options(joinedload(Question.options), joinedload(Question.progress))
        .filter(Question.bank_id == bank_id)
    )
    questions = query.order_by(Question.source_order.asc(), Question.id.asc()).all()

    def prog(q: Question) -> QuestionProgress | None:
        return q.progress

    if mode == "wrong":
        questions = [q for q in questions if prog(q) and prog(q).is_wrong]
    elif mode == "favorite":
        questions = [q for q in questions if prog(q) and prog(q).is_favorite]
    elif mode == "unanswered":
        questions = [q for q in questions if not prog(q) or not prog(q).answered]
    elif mode == "random":
        questions = list(questions)
        random.shuffle(questions)
    # sequence: keep order
    return questions


def submit_answer(
    db: Session,
    question_id: int,
    user_answer: list[str],
) -> dict:
    question = (
        db.query(Question)
        .options(joinedload(Question.progress))
        .filter(Question.id == question_id)
        .first()
    )
    if question is None:
        raise ValueError("question not found")

    correct = question.answer
    normalized_user = sorted(a.upper() if len(a) == 1 and a.isalpha() else a for a in user_answer)
    normalized_correct = None
    is_correct = False
    if correct is not None:
        normalized_correct = sorted(
            a.upper() if len(a) == 1 and a.isalpha() else a for a in correct
        )
        is_correct = normalized_user == normalized_correct

    record = AnswerRecord(
        question_id=question.id,
        user_answer=user_answer,
        is_correct=is_correct,
    )
    db.add(record)

    progress = question.progress
    if progress is None:
        progress = QuestionProgress(question_id=question.id)
        db.add(progress)
        db.flush()

    progress.answered = True
    progress.last_answered_at = datetime.utcnow()
    if is_correct:
        progress.correct_count += 1
        progress.is_wrong = False
    else:
        progress.wrong_count += 1
        progress.is_wrong = True

    db.commit()
    return {
        "is_correct": is_correct,
        "correct_answer": correct,
        "explanation": question.explanation,
    }


def set_favorite(db: Session, question_id: int, is_favorite: bool) -> Question:
    question = (
        db.query(Question)
        .options(joinedload(Question.progress), joinedload(Question.options))
        .filter(Question.id == question_id)
        .first()
    )
    if question is None:
        raise ValueError("question not found")
    progress = question.progress
    if progress is None:
        progress = QuestionProgress(question_id=question.id, is_favorite=is_favorite)
        db.add(progress)
    else:
        progress.is_favorite = is_favorite
    db.commit()
    db.refresh(question)
    return question
