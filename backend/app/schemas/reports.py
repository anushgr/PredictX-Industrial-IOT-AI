from pydantic import BaseModel


class ReportExportRequest(BaseModel):
    type: str
    format: str


class ReportExportResponse(BaseModel):
    url: str
    status: str = "queued"
