from __future__ import annotations

import json
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database.db import get_db
from ..schemas.schemas import BackupImportResult
from ..services import backup_service

router = APIRouter(prefix="/api/backups", tags=["backups"])


@router.get("/export")
def export_backup(db: Session = Depends(get_db)):
    payload = backup_service.export_backup(db)
    content = backup_service.dumps_backup(payload).encode("utf-8")
    return StreamingResponse(
        BytesIO(content),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=question_bank_backup.json"},
    )


@router.post("/import", response_model=BackupImportResult)
async def import_backup(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid json: {exc}") from exc
    result = backup_service.import_backup(db, payload, replace=False)
    return BackupImportResult(**result)
