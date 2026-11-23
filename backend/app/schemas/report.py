from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "xlsx"
    CSV = "csv"


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportTemplate(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    SALES_ANALYSIS = "sales_analysis"
    CUSTOMER_REPORT = "customer_report"
    FORECAST_REPORT = "forecast_report"
    DATA_QUALITY = "data_quality"
    CUSTOM = "custom"


class ReportBase(BaseModel):
    title: str
    description: Optional[str] = None
    dataset_id: str
    template: ReportTemplate = ReportTemplate.CUSTOM
    format: ReportFormat = ReportFormat.PDF
    config: Dict[str, Any] = Field(default_factory=dict)


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ReportStatus] = None
    file_path: Optional[str] = None
    error_message: Optional[str] = None


class Report(ReportBase):
    id: str
    status: ReportStatus = ReportStatus.PENDING
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: List[Report]
    total: int
    page: int
    page_size: int


class ReportResponse(BaseModel):
    report: Report