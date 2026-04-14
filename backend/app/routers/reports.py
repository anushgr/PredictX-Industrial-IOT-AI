from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas.reports import ReportExportRequest, ReportExportResponse

router = APIRouter()


@router.post("/reports/export", response_model=ReportExportResponse)
def export_report(payload: ReportExportRequest, _: dict = Depends(get_current_user)) -> ReportExportResponse:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    filename = f"{payload.type.replace(' ', '-').lower()}-{ts}.{payload.format.lower()}"
    return ReportExportResponse(url=f"/exports/{filename}", status="queued")
