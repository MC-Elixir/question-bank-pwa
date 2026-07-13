from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.db import get_db
from ..schemas.schemas import AnswerRequest, AnswerResponse, FavoriteRequest, OptionSchema, QuestionOut
from ..services import practice_service

router = APIRouter(prefix="/api/questions", tags=["questions"])


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


@router.post("/{question_id}/answer", response_model=AnswerResponse)
def answer_question(
    question_id: int,
    body: AnswerRequest,
    db: Session = Depends(get_db),
):
    try:
        result = practice_service.submit_answer(db, question_id, body.answer)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AnswerResponse(**result)


@router.put("/{question_id}/favorite", response_model=QuestionOut)
def favorite_question(
    question_id: int,
    body: FavoriteRequest,
    db: Session = Depends(get_db),
):
    try:
        q = practice_service.set_favorite(db, question_id, body.is_favorite)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _question_out(q)
