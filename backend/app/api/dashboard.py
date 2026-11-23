from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
import structlog
from datetime import datetime
from uuid import uuid4

from app.schemas.dashboard import (
    Dashboard,
    DashboardCreate,
    DashboardUpdate,
    DashboardListResponse,
    DashboardResponse,
    DashboardWidget,
    ChartConfig,
    ChartType,
    AxisConfig,
    SeriesConfig,
)
from app.services.ingestion.service import ingestion_service
from app.services.visualization.service import visualization_service

logger = structlog.get_logger()

router = APIRouter(prefix="/dashboards", tags=["dashboards"])

DASHBOARDS: dict = {}


def _get_dataset_columns(dataset_id: str) -> List[str]:
    try:
        df = ingestion_service.load_dataframe(dataset_id)
        return df.columns.tolist()
    except Exception:
        return []


def _create_default_widgets(dataset_id: str) -> List[DashboardWidget]:
    widgets = []
    suggestions = visualization_service.suggest_charts(dataset_id)
    
    x_pos = 0
    y_pos = 0
    
    for idx, suggestion in enumerate(suggestions[:6]):
        chart_type = suggestion["chart_type"]
        x_col = suggestion.get("x_column", "")
        y_cols = suggestion.get("y_columns", [])
        
        if chart_type in ["pie", "donut"] and x_col:
            config = ChartConfig(
                type=ChartType(chart_type),
                title=suggestion.get("title", ""),
                x_axis=AxisConfig(name=x_col, type="category"),
                y_axis=AxisConfig(name="Value", type="value"),
                series=[SeriesConfig(name="Distribution", data=[])],
            )
        elif chart_type in ["histogram"] and x_col:
            config = ChartConfig(
                type=ChartType(chart_type),
                title=suggestion.get("title", ""),
                x_axis=AxisConfig(name=x_col, type="value"),
                y_axis=AxisConfig(name="Frequency", type="value"),
                series=[SeriesConfig(name=x_col, data=[])],
            )
        elif chart_type in ["scatter"] and x_col and y_cols:
            config = ChartConfig(
                type=ChartType(chart_type),
                title=suggestion.get("title", ""),
                x_axis=AxisConfig(name=x_col, type="value"),
                y_axis=AxisConfig(name=y_cols[0], type="value"),
                series=[SeriesConfig(name="Scatter", data=[])],
            )
        elif chart_type in ["heatmap"] and y_cols:
            config = ChartConfig(
                type=ChartType(chart_type),
                title=suggestion.get("title", ""),
                x_axis=AxisConfig(name="Variables", type="category"),
                y_axis=AxisConfig(name="Variables", type="category"),
                series=[SeriesConfig(name="Correlation", data=[])],
            )
        else:
            config = ChartConfig(
                type=ChartType(chart_type),
                title=suggestion.get("title", ""),
                x_axis=AxisConfig(name=x_col, type="category"),
                y_axis=AxisConfig(name=y_cols[0] if y_cols else "Value", type="value"),
                series=[SeriesConfig(name=y_cols[0] if y_cols else "Value", data=[])],
            )

        widget = DashboardWidget(
            id=str(uuid4()),
            title=suggestion.get("title", f"Chart {idx + 1}"),
            chart_type=ChartType(chart_type),
            config=config,
            dataset_id=dataset_id,
            x=x_pos,
            y=y_pos,
            w=6,
            h=4,
        )
        widgets.append(widget)
        
        x_pos += 6
        if x_pos >= 12:
            x_pos = 0
            y_pos += 4

    return widgets


@router.post("", response_model=DashboardResponse)
async def create_dashboard(dashboard: DashboardCreate):
    dashboard_id = str(uuid4())
    now = datetime.utcnow()
    
    widgets = _create_default_widgets(dashboard.dataset_id)
    
    new_dashboard = Dashboard(
        id=dashboard_id,
        name=dashboard.name,
        description=dashboard.description,
        dataset_id=dashboard.dataset_id,
        widgets=widgets,
        created_at=now,
        updated_at=now,
    )
    
    DASHBOARDS[dashboard_id] = new_dashboard
    
    return DashboardResponse(dashboard=new_dashboard)


@router.get("", response_model=DashboardListResponse)
async def list_dashboards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    dataset_id: Optional[str] = Query(None),
):
    dashboards = list(DASHBOARDS.values())
    
    if dataset_id:
        dashboards = [d for d in dashboards if d.dataset_id == dataset_id]
    
    total = len(dashboards)
    start = (page - 1) * page_size
    end = start + page_size
    
    return DashboardListResponse(
        dashboards=dashboards[start:end],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(dashboard_id: str):
    if dashboard_id not in DASHBOARDS:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return DashboardResponse(dashboard=DASHBOARDS[dashboard_id])


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(dashboard_id: str, update: DashboardUpdate):
    if dashboard_id not in DASHBOARDS:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    dashboard = DASHBOARDS[dashboard_id]
    
    if update.name is not None:
        dashboard.name = update.name
    if update.description is not None:
        dashboard.description = update.description
    if update.widgets is not None:
        dashboard.widgets = update.widgets
    
    dashboard.updated_at = datetime.utcnow()
    
    return DashboardResponse(dashboard=dashboard)


@router.delete("/{dashboard_id}")
async def delete_dashboard(dashboard_id: str):
    if dashboard_id not in DASHBOARDS:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    del DASHBOARDS[dashboard_id]
    return {"message": "Dashboard deleted successfully"}


@router.post("/{dashboard_id}/widgets", response_model=DashboardWidget)
async def add_widget(dashboard_id: str, widget: DashboardWidget):
    if dashboard_id not in DASHBOARDS:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    if not widget.id:
        widget.id = str(uuid4())
    
    DASHBOARDS[dashboard_id].widgets.append(widget)
    DASHBOARDS[dashboard_id].updated_at = datetime.utcnow()
    
    return widget


@router.patch("/{dashboard_id}/widgets/{widget_id}", response_model=DashboardWidget)
async def update_widget(dashboard_id: str, widget_id: str, update: DashboardWidget):
    if dashboard_id not in DASHBOARDS:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    dashboard = DASHBOARDS[dashboard_id]
    for i, widget in enumerate(dashboard.widgets):
        if widget.id == widget_id:
            dashboard.widgets[i] = update
            dashboard.updated_at = datetime.utcnow()
            return update
    
    raise HTTPException(status_code=404, detail="Widget not found")


@router.delete("/{dashboard_id}/widgets/{widget_id}")
async def delete_widget(dashboard_id: str, widget_id: str):
    if dashboard_id not in DASHBOARDS:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    dashboard = DASHBOARDS[dashboard_id]
    dashboard.widgets = [w for w in dashboard.widgets if w.id != widget_id]
    dashboard.updated_at = datetime.utcnow()
    
    return {"message": "Widget deleted successfully"}


@router.post("/{dashboard_id}/refresh")
async def refresh_dashboard(dashboard_id: str):
    if dashboard_id not in DASHBOARDS:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    dashboard = DASHBOARDS[dashboard_id]
    
    refreshed_widgets = []
    for widget in dashboard.widgets:
        try:
            chart_data = visualization_service.generate_chart_data(
                dataset_id=widget.dataset_id,
                chart_type=widget.chart_type.value,
                x_column=widget.config.x_axis.name or "",
                y_columns=[s.name for s in widget.config.series],
                group_by=None,
                filters=None,
                aggregation=None,
                limit=1000,
            )
            
            updated_widget = widget.model_copy()
            updated_widget.config.series = [
                SeriesConfig(
                    name=s.name,
                    data=chart_data.get("series", [{}])[i].get("data", []) if i < len(chart_data.get("series", [])) else [],
                    type=s.type,
                    color=s.color,
                    y_axis_index=s.y_axis_index,
                )
                for i, s in enumerate(widget.config.series)
            ]
            updated_widget.config.categories = chart_data.get("categories", [])
            
            refreshed_widgets.append(updated_widget)
        except Exception as e:
            logger.error("widget_refresh_failed", widget_id=widget.id, error=str(e))
            refreshed_widgets.append(widget)
    
    dashboard.widgets = refreshed_widgets
    dashboard.updated_at = datetime.utcnow()
    
    return DashboardResponse(dashboard=dashboard)