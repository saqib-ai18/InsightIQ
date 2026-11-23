import pandas as pd
import structlog
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from pathlib import Path
import io
import json

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from app.services.ingestion.service import ingestion_service
from app.services.profiling.service import profiling_service
from app.services.analytics.service import analytics_service
from app.services.visualization.service import visualization_service
from app.schemas.report import (
    Report, ReportStatus, ReportFormat, ReportTemplate, ReportCreate
)
from app.core.config import get_settings

logger = structlog.get_logger()


class ReportingService:
    def __init__(self):
        self.settings = get_settings()
        self.reports_dir = Path(self.settings.UPLOAD_DIR) / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.reports: Dict[str, Report] = {}

    def create_report(self, report_data: ReportCreate) -> Report:
        report_id = str(uuid4())
        now = datetime.utcnow()
        
        report = Report(
            id=report_id,
            title=report_data.title,
            description=report_data.description,
            dataset_id=report_data.dataset_id,
            template=report_data.template,
            format=report_data.format,
            config=report_data.config,
            status=ReportStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        
        self.reports[report_id] = report
        return report

    def get_report(self, report_id: str) -> Optional[Report]:
        return self.reports.get(report_id)

    def list_reports(self, page: int = 1, page_size: int = 20, dataset_id: Optional[str] = None) -> List[Report]:
        reports = list(self.reports.values())
        
        if dataset_id:
            reports = [r for r in reports if r.dataset_id == dataset_id]
        
        reports.sort(key=lambda r: r.created_at, reverse=True)
        
        start = (page - 1) * page_size
        end = start + page_size
        return reports[start:end]

    def delete_report(self, report_id: str) -> bool:
        if report_id in self.reports:
            report = self.reports[report_id]
            if report.file_path:
                try:
                    Path(report.file_path).unlink(missing_ok=True)
                except Exception:
                    pass
            del self.reports[report_id]
            return True
        return False

    async def generate_report(self, report_id: str) -> Report:
        report = self.reports.get(report_id)
        if not report:
            raise ValueError("Report not found")
        
        report.status = ReportStatus.PROCESSING
        report.updated_at = datetime.utcnow()
        
        try:
            df = ingestion_service.load_dataframe(report.dataset_id)
            
            if report.format == ReportFormat.PDF:
                file_path = await self._generate_pdf(report, df)
            elif report.format == ReportFormat.EXCEL:
                file_path = await self._generate_excel(report, df)
            elif report.format == ReportFormat.CSV:
                file_path = await self._generate_csv(report, df)
            else:
                raise ValueError(f"Unsupported format: {report.format}")
            
            file_size = Path(file_path).stat().st_size
            report.file_path = file_path
            report.file_size = file_size
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error("report_generation_failed", report_id=report_id, error=str(e))
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
        
        report.updated_at = datetime.utcnow()
        return report

    async def _generate_pdf(self, report: Report, df: pd.DataFrame) -> str:
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab not installed. Install with: pip install reportlab")
        
        file_path = str(self.reports_dir / f"{report.id}.pdf")
        
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#1f2937'),
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor('#374151'),
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=14,
        )
        
        story = []
        
        story.append(Paragraph(report.title, title_style))
        story.append(Spacer(1, 20))
        
        if report.description:
            story.append(Paragraph(report.description, body_style))
            story.append(Spacer(1, 12))
        
        story.append(Paragraph("Dataset Overview", heading_style))
        
        overview_data = [
            ["Dataset ID", report.dataset_id],
            ["Rows", f"{len(df):,}"],
            ["Columns", f"{len(df.columns)}"],
            ["Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ]
        
        table = Table(overview_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        if report.template == ReportTemplate.DATA_QUALITY:
            story.extend(self._generate_data_quality_section(df, heading_style, body_style))
        elif report.template == ReportTemplate.EXECUTIVE_SUMMARY:
            story.extend(self._generate_executive_summary(df, heading_style, body_style))
        elif report.template == ReportTemplate.SALES_ANALYSIS:
            story.extend(self._generate_sales_analysis(df, heading_style, body_style))
        else:
            story.extend(self._generate_generic_analysis(df, heading_style, body_style))
        
        doc.build(story)
        return file_path

    def _generate_data_quality_section(self, df: pd.DataFrame, heading_style, body_style) -> List:
        story = []
        story.append(Paragraph("Data Quality Analysis", heading_style))
        
        profile = profiling_service.profile_dataset(df=df)
        
        story.append(Paragraph(f"Overall Quality Score: {profile.quality_score}/100", body_style))
        story.append(Spacer(1, 10))
        
        issues_data = [["Column", "Issue Type", "Severity", "Count", "Message"]]
        for issue in profile.quality_issues[:20]:
            issues_data.append([
                issue.column,
                issue.type.value,
                issue.severity,
                str(issue.count),
                issue.message[:80] + "..." if len(issue.message) > 80 else issue.message,
            ])
        
        if len(issues_data) > 1:
            table = Table(issues_data, colWidths=[1*inch, 1*inch, 0.7*inch, 0.5*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ]))
            story.append(table)
        
        if profile.recommendations:
            story.append(Spacer(1, 12))
            story.append(Paragraph("Recommendations", heading_style))
            for rec in profile.recommendations:
                story.append(Paragraph(f"• {rec}", body_style))
        
        return story

    def _generate_executive_summary(self, df: pd.DataFrame, heading_style, body_style) -> List:
        story = []
        story.append(Paragraph("Executive Summary", heading_style))
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        story.append(Paragraph(f"This dataset contains {len(df):,} rows and {len(df.columns)} columns.", body_style))
        story.append(Paragraph(f"There are {len(numeric_cols)} numeric and {len(categorical_cols)} categorical columns.", body_style))
        
        if numeric_cols:
            story.append(Paragraph("Key Metrics", heading_style))
            for col in numeric_cols[:5]:
                summary = analytics_service.statistical_summary(df, [col])
                if col in summary:
                    s = summary[col]
                    story.append(Paragraph(f"<b>{col}:</b> Mean={s['mean']:.2f}, Median={s['median']:.2f}, Range=[{s['min']:.2f}, {s['max']:.2f}]", body_style))
        
        return story

    def _generate_sales_analysis(self, df: pd.DataFrame, heading_style, body_style) -> List:
        story = []
        story.append(Paragraph("Sales Analysis", heading_style))
        
        date_cols = df.select_dtypes(include=['datetime', 'date']).columns.tolist()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if date_cols and numeric_cols:
            date_col = date_cols[0]
            value_col = numeric_cols[0]
            
            trend = analytics_service.trend_analysis(df, date_col, value_col)
            story.append(Paragraph(f"Trend: {trend['trend']} (R²={trend['r_squared']:.3f})", body_style))
            
            growth = analytics_service.growth_rate(df, value_col, date_col, "M")
            story.append(Paragraph(f"Monthly Growth: {growth[f'{value_col}_growth'].iloc[-1] if len(growth) > 0 else 'N/A'}%", body_style))
        
        return story

    def _generate_generic_analysis(self, df: pd.DataFrame, heading_style, body_style) -> List:
        story = []
        story.append(Paragraph("Data Analysis", heading_style))
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            story.append(Paragraph("Statistical Summary", heading_style))
            summary = analytics_service.statistical_summary(df, numeric_cols[:5])
            
            stats_data = [["Column", "Count", "Mean", "Std", "Min", "Max"]]
            for col, stats in summary.items():
                stats_data.append([
                    col,
                    str(stats['count']),
                    f"{stats['mean']:.2f}",
                    f"{stats['std']:.2f}",
                    f"{stats['min']:.2f}",
                    f"{stats['max']:.2f}",
                ])
            
            table = Table(stats_data, colWidths=[1.2*inch, 0.7*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ]))
            story.append(table)
        
        return story

    async def _generate_excel(self, report: Report, df: pd.DataFrame) -> str:
        if not OPENPYXL_AVAILABLE:
            raise RuntimeError("openpyxl not installed. Install with: pip install openpyxl")
        
        file_path = str(self.reports_dir / f"{report.id}.xlsx")
        
        wb = Workbook()
        
        ws_overview = wb.active
        ws_overview.title = "Overview"
        
        headers = ["Property", "Value"]
        for col, header in enumerate(headers, 1):
            cell = ws_overview.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
        
        overview_data = [
            ["Dataset ID", report.dataset_id],
            ["Rows", len(df)],
            ["Columns", len(df.columns)],
            ["Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ]
        
        for row_idx, (key, value) in enumerate(overview_data, 2):
            ws_overview.cell(row=row_idx, column=1, value=key)
            ws_overview.cell(row=row_idx, column=2, value=value)
        
        ws_data = wb.create_sheet("Data Preview")
        for col_idx, col_name in enumerate(df.columns, 1):
            cell = ws_data.cell(row=1, column=col_idx, value=col_name)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
        
        for row_idx, row in df.head(100).iterrows():
            for col_idx, value in enumerate(row, 1):
                ws_data.cell(row=row_idx + 1, column=col_idx, value=value)
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            ws_stats = wb.create_sheet("Statistics")
            summary = analytics_service.statistical_summary(df, numeric_cols)
            
            stats_headers = ["Column", "Count", "Mean", "Median", "Std", "Min", "Max", "Q25", "Q75", "Skewness", "Kurtosis"]
            for col_idx, header in enumerate(stats_headers, 1):
                cell = ws_stats.cell(row=1, column=col_idx, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
            
            for row_idx, (col, stats) in enumerate(summary.items(), 2):
                ws_stats.cell(row=row_idx, column=1, value=col)
                ws_stats.cell(row=row_idx, column=2, value=stats['count'])
                ws_stats.cell(row=row_idx, column=3, value=stats['mean'])
                ws_stats.cell(row=row_idx, column=4, value=stats['median'])
                ws_stats.cell(row=row_idx, column=5, value=stats['std'])
                ws_stats.cell(row=row_idx, column=6, value=stats['min'])
                ws_stats.cell(row=row_idx, column=7, value=stats['max'])
                ws_stats.cell(row=row_idx, column=8, value=stats['q25'])
                ws_stats.cell(row=row_idx, column=9, value=stats['q75'])
                ws_stats.cell(row=row_idx, column=10, value=stats['skewness'])
                ws_stats.cell(row=row_idx, column=11, value=stats['kurtosis'])
        
        if report.template == ReportTemplate.DATA_QUALITY:
            ws_quality = wb.create_sheet("Data Quality")
            profile = profiling_service.profile_dataset(df=df)
            
            quality_headers = ["Column", "Issue Type", "Severity", "Count", "Message"]
            for col_idx, header in enumerate(quality_headers, 1):
                cell = ws_quality.cell(row=1, column=col_idx, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
            
            for row_idx, issue in enumerate(profile.quality_issues, 2):
                ws_quality.cell(row=row_idx, column=1, value=issue.column)
                ws_quality.cell(row=row_idx, column=2, value=issue.type.value)
                ws_quality.cell(row=row_idx, column=3, value=issue.severity)
                ws_quality.cell(row=row_idx, column=4, value=issue.count)
                ws_quality.cell(row=row_idx, column=5, value=issue.message)
        
        for ws in wb.worksheets:
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column].width = adjusted_width
        
        wb.save(file_path)
        return file_path

    async def _generate_csv(self, report: Report, df: pd.DataFrame) -> str:
        file_path = str(self.reports_dir / f"{report.id}.csv")
        df.to_csv(file_path, index=False)
        return file_path


reporting_service = ReportingService()