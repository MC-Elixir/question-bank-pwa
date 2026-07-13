from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, joinedload

from ..database.models import (
    AnswerRecord,
    Question,
    QuestionBank,
    QuestionOption,
    QuestionProgress,
)


def export_backup(db: Session) -> dict[str, Any]:
    banks = (
        db.query(QuestionBank)
        .options(
            joinedload(QuestionBank.questions)
            .joinedload(Question.options),
            joinedload(QuestionBank.questions)
            .joinedload(Question.progress),
            joinedload(QuestionBank.questions)
            .joinedload(Question.answer_records),
        )
        .all()
    )
    payload = {
        "version": 1,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "banks": [],
    }
    for bank in banks:
        bank_data = {
            "name": bank.name,
            "description": bank.description,
            "created_at": bank.created_at.isoformat() if bank.created_at else None,
            "questions": [],
        }
        for q in sorted(bank.questions, key=lambda x: (x.source_order, x.id)):
            bank_data["questions"].append(
                {
                    "chapter": q.chapter,
                    "question_type": q.question_type,
                    "stem": q.stem,
                    "answer": q.answer,
                    "explanation": q.explanation,
                    "source_order": q.source_order,
                    "needs_review": q.needs_review,
                    "content_hash": q.content_hash,
                    "options": [
                        {
                            "label": o.label,
                            "content": o.content,
                            "sort_order": o.sort_order,
                        }
                        for o in q.options
                    ],
                    "progress": None
                    if not q.progress
                    else {
                        "is_favorite": q.progress.is_favorite,
                        "is_wrong": q.progress.is_wrong,
                        "answered": q.progress.answered,
                        "correct_count": q.progress.correct_count,
                        "wrong_count": q.progress.wrong_count,
                    },
                    "answer_records": [
                        {
                            "user_answer": r.user_answer,
                            "is_correct": r.is_correct,
                            "answered_at": r.answered_at.isoformat()
                            if r.answered_at
                            else None,
                        }
                        for r in q.answer_records
                    ],
                }
            )
        payload["banks"].append(bank_data)
    return payload


def import_backup(db: Session, payload: dict[str, Any], replace: bool = False) -> dict:
    if replace:
        db.query(AnswerRecord).delete()
        db.query(QuestionProgress).delete()
        db.query(QuestionOption).delete()
        db.query(Question).delete()
        db.query(QuestionBank).delete()
        db.commit()

    bank_count = 0
    question_count = 0
    for bank_data in payload.get("banks", []):
        bank = QuestionBank(
            name=bank_data.get("name") or "恢复题库",
            description=bank_data.get("description"),
        )
        db.add(bank)
        db.flush()
        bank_count += 1
        for item in bank_data.get("questions", []):
            q = Question(
                bank_id=bank.id,
                chapter=item.get("chapter"),
                question_type=item.get("question_type") or "unknown",
                stem=item.get("stem") or "",
                answer=item.get("answer"),
                explanation=item.get("explanation"),
                source_order=item.get("source_order") or 0,
                needs_review=bool(item.get("needs_review")),
                content_hash=item.get("content_hash"),
            )
            db.add(q)
            db.flush()
            question_count += 1
            for opt in item.get("options") or []:
                db.add(
                    QuestionOption(
                        question_id=q.id,
                        label=opt.get("label") or "",
                        content=opt.get("content") or "",
                        sort_order=opt.get("sort_order") or 0,
                    )
                )
            prog = item.get("progress") or {}
            db.add(
                QuestionProgress(
                    question_id=q.id,
                    is_favorite=bool(prog.get("is_favorite")),
                    is_wrong=bool(prog.get("is_wrong")),
                    answered=bool(prog.get("answered")),
                    correct_count=int(prog.get("correct_count") or 0),
                    wrong_count=int(prog.get("wrong_count") or 0),
                )
            )
            for rec in item.get("answer_records") or []:
                answered_at = None
                if rec.get("answered_at"):
                    try:
                        answered_at = datetime.fromisoformat(
                            rec["answered_at"].replace("Z", "")
                        )
                    except Exception:
                        answered_at = datetime.utcnow()
                db.add(
                    AnswerRecord(
                        question_id=q.id,
                        user_answer=rec.get("user_answer") or [],
                        is_correct=bool(rec.get("is_correct")),
                        answered_at=answered_at or datetime.utcnow(),
                    )
                )
    db.commit()
    return {
        "banks": bank_count,
        "questions": question_count,
        "message": "backup imported",
    }


def dumps_backup(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
