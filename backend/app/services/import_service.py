from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional, Union

from sqlalchemy.orm import Session

from ..database.models import ImportJob, Question, QuestionBank, QuestionOption, QuestionProgress
from ..schemas.schemas import ParsedQuestionSchema
from .duplicate_detector import mark_duplicates
from .question_parser import parse_questions
from .question_validator import ValidatedQuestion, validate_questions

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _to_schema(q: ValidatedQuestion) -> dict:
    return {
        "chapter": q.chapter,
        "question_type": q.question_type,
        "stem": q.stem,
        "options": q.options,
        "answer": q.answer,
        "explanation": q.explanation,
        "source_order": q.source_order,
        "needs_review": q.needs_review,
        "issues": q.issues,
        "content_hash": q.content_hash,
        "duplicate_of": q.duplicate_of,
    }


def _existing_hashes(db: Session, bank_name: str) -> dict[str, int]:
    banks = db.query(QuestionBank).filter(QuestionBank.name == bank_name).all()
    result: dict[str, int] = {}
    for bank in banks:
        for q in bank.questions:
            if q.content_hash:
                result[q.content_hash] = q.id
    return result


def preview_import(
    db: Session,
    fileobj: Union[BinaryIO, str, Path],
    bank_name: str,
    filename: Optional[str] = None,
) -> ImportJob:
    raws = parse_questions(fileobj)
    validated = validate_questions(raws)
    validated = mark_duplicates(validated, _existing_hashes(db, bank_name))
    payload = [_to_schema(q) for q in validated]
    error_count = sum(1 for q in validated if q.issues)

    job = ImportJob(
        bank_name=bank_name,
        status="preview",
        source_filename=filename,
        preview_payload={"questions": payload},
        question_count=len(payload),
        error_count=error_count,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_import_job(db: Session, job_id: int) -> Optional[ImportJob]:
    return db.query(ImportJob).filter(ImportJob.id == job_id).first()


def confirm_import(
    db: Session,
    job_id: int,
    questions: Optional[list[ParsedQuestionSchema]] = None,
) -> ImportJob:
    job = get_import_job(db, job_id)
    if job is None:
        raise ValueError("import job not found")
    if job.status == "confirmed":
        return job

    if questions is not None:
        payload = [q.model_dump() for q in questions]
    else:
        payload = (job.preview_payload or {}).get("questions", [])

    bank = QuestionBank(name=job.bank_name)
    db.add(bank)
    db.flush()

    for item in payload:
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
        for opt in item.get("options") or []:
            db.add(
                QuestionOption(
                    question_id=q.id,
                    label=opt.get("label") or "",
                    content=opt.get("content") or "",
                    sort_order=opt.get("sort_order") or 0,
                )
            )
        db.add(QuestionProgress(question_id=q.id))

    job.bank_id = bank.id
    job.status = "confirmed"
    job.confirmed_at = datetime.utcnow()
    job.preview_payload = {"questions": payload}
    job.question_count = len(payload)
    job.error_count = sum(1 for x in payload if x.get("issues"))
    db.commit()
    db.refresh(job)
    return job
