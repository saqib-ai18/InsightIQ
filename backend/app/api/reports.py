from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from datetime import datetime
import structlog
from starlette.responses import FileResponse

from app.schemas.report import (
    Report,
    ReportCreate,
    ReportUpdate,
    ReportListResponse,
    ReportResponse,
    ReportFormat,
    ReportTemplate,
    ReportStatus,
)
from app.services.reporting.service import reporting_service

logger = structlog.get_logger()

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportResponse)
async def create_report(report: ReportCreate):
    new_report = reporting_service.create_report(report)
    return ReportResponse(report=new_report)


@router.get("", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    dataset_id: Optional[str] = Query(None),
):
    reports = reporting_service.list_reports(page, page_size, dataset_id)
    total = len([r for r in reporting_service.reports.values() if not dataset_id or r.dataset_id == dataset_id])
    
    return ReportListResponse(
        reports=reports,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str):
    report = reporting_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse(report=report)


@router.post("/{report_id}/generate")
async def generate_report(report_id: str):
    report = reporting_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = await reporting_service.generate_report(report_id)
    return ReportResponse(report=report)


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    report = reporting_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report not ready for download")
    
    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file not found")
    
    media_types = {
        ReportFormat.PDF: "application/pdf",
        ReportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ReportFormat.CSV: "text/csv",
    }
    
    extensions = {
        ReportFormat.PDF: ".pdf",
        ReportFormat.EXCEL: ".xlsx",
        ReportFormat.CSV: ".csv",
    }
    
    return FileResponse(
        path=report.file_path,
        media_type=media_types.get(report.format, "application/octet-stream"),
        filename=f"{report.title.replace(' ', '_')}{extensions.get(report.format, '')}",
    )


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(report_id: str, update: ReportUpdate):
    report = reporting_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if update.title is not None:
        report.title = update.title
    if update.description is not None:
        report.description = update.description
    if update.status is not None:
        report.status = update.status
    if update.file_path is not None:
        report.file_path = update.file_path
    if update.error_message is not None:
        report.error_message = update.error_message
    
    report.updated_at = datetime.utcnow()
    
    return ReportResponse(report=report)


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    success = reporting_service.delete_report(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted successfully"}


@router.get("/templates/list")
async def list_templates():
    return {
        "templates": [
            {
                "id": ReportTemplate.EXECUTIVE_SUMMARY,
                "name": "Executive Summary",
                "description": "High-level overview with key metrics and insights",
            },
            {
                "id": ReportTemplate.SALES_ANALYSIS,
                "name": "Sales Analysis",
                "description": "Revenue trends, growth rates, and top products",
            },
            {
                "id": ReportTemplate.CUSTOMER_REPORT,
                "name": "Customer Report",
                "description": "Segmentation, behavior, and lifetime value analysis",
            },
            {
                "id": ReportTemplate.FORECAST_REPORT,
                "name": "Forecast Report",
                "description": "Predictions with confidence intervals",
            },
            {
                "id": ReportTemplate.DATA_QUALITY,
                "name": "Data Quality Report",
                "description": "Comprehensive data profiling and quality assessment",
            },
        ]
    }