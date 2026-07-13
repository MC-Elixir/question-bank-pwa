from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..database.db import get_db
from ..database.models import QuestionBank
from ..schemas.schemas import OptionSchema, QuestionBankSchema, QuestionOut
from ..services import practice_service

router = APIRouter(prefix="/api/question-banks", tags=["question-banks"])


@router.get("", response_model=list[QuestionBankSchema])
def list_banks(db: Session = Depends(get_db)):
    banks = db.query(QuestionBank).order_by(QuestionBank.id.asc()).all()
    result = []
    for bank in banks:
        result.append(
            QuestionBankSchema(
                id=bank.id,
                name=bank.name,
                description=bank.description,
                question_count=len(bank.questions),
                created_at=bank.created_at,
                updated_at=bank.updated_at,
            )
        )
    return result


def _question_out(q) -> QuestionOut:
    progress = q.progress
    return QuestionOut(
        id=q.id,
        bank_id=q.bank_id,
        chapter=q.chapter,
        question_type=q.question_type,
        stem=q.stem,
        options=[
            OptionSchema(label=o.label, content=o.content, sort_order=o.sort_order)
            for o in q.options
        ],
        answer=q.answer,
        explanation=q.explanation,
        source_order=q.source_order,
        needs_review=q.needs_review,
        is_favorite=bool(progress.is_favorite) if progress else False,
        is_wrong=bool(progress.is_wrong) if progress else False,
        answered=bool(progress.answered) if progress else False,
    )


@router.get("/{bank_id}/questions", response_model=list[QuestionOut])
def list_bank_questions(
    bank_id: int,
    mode: str = Query("sequence", pattern="^(sequence|random|wrong|favorite|unanswered)$"),
    db: Session = Depends(get_db),
):
    bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
    if bank is None:
        raise HTTPException(status_code=404, detail="question bank not found")
    questions = practice_service.list_questions(db, bank_id, mode=mode)
    return [_question_out(q) for q in questions]
