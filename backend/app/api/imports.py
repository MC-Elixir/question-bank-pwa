from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database.db import get_db
from ..schemas.schemas import ImportConfirmRequest, ImportPreviewResponse, ParsedQuestionSchema
from ..services import import_service

router = APIRouter(prefix="/api/imports", tags=["imports"])


def _job_to_response(job) -> ImportPreviewResponse:
    payload = job.preview_payload or {}
    questions = [ParsedQuestionSchema(**q) for q in payload.get("questions", [])]
    return ImportPreviewResponse(
        id=job.id,
        bank_name=job.bank_name,
        status=job.status,
        source_filename=job.source_filename,
        question_count=job.question_count,
        error_count=job.error_count,
        questions=questions,
        created_at=job.created_at,
        bank_id=job.bank_id,
    )


@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_import(
    file: UploadFile = File(...),
    bank_name: str = Form(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    from io import BytesIO

    try:
        job = import_service.preview_import(
            db, BytesIO(data), bank_name=bank_name, filename=file.filename
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"parse failed: {exc}") from exc
    return _job_to_response(job)


@router.get("/{job_id}", response_model=ImportPreviewResponse)
def get_import(job_id: int, db: Session = Depends(get_db)):
    job = import_service.get_import_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="import job not found")
    return _job_to_response(job)


@router.post("/{job_id}/confirm", response_model=ImportPreviewResponse)
def confirm_import(
    job_id: int,
    body: ImportConfirmRequest | None = None,
    db: Session = Depends(get_db),
):
    try:
        questions = body.questions if body else None
        job = import_service.confirm_import(db, job_id, questions=questions)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _job_to_response(job)
