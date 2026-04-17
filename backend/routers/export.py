"""Export functionality for filtered data."""
import io
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas.common import ExportRequest
from backend.services.auth_service import get_current_user
from backend.services.export_service import (
    build_export_data,
    build_docx_export,
    build_entity_docx_export,
    build_resume_pdf_export,
)

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/items")
def export_items(req: ExportRequest, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    if req.format == "docx":
        try:
            if req.entity_type:
                buf, filename = build_entity_docx_export(db, req)
            else:
                buf, filename = build_docx_export(db, req)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        ascii_filename = "showcase_export.docx"
        quoted_filename = quote(filename)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={ascii_filename}; filename*=UTF-8''{quoted_filename}"
            }
        )
    if req.format == "pdf":
        try:
            buf, filename = build_resume_pdf_export(db, req.person_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        ascii_filename = "showcase_export.pdf"
        quoted_filename = quote(filename)
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={ascii_filename}; filename*=UTF-8''{quoted_filename}"
            }
        )

    data, columns = build_export_data(db, req)

    if req.format == "json":
        return {"data": data, "columns": columns}

    elif req.format == "xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = req.entity_type
        ws.append(columns)
        for row in data:
            ws.append([row.get(c, "") for c in columns])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={req.entity_type}_export.xlsx"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
