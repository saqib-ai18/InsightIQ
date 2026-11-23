from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class ChartType(str, Enum):
    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    BUBBLE = "bubble"
    HISTOGRAM = "histogram"
    BOX = "box"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    RADAR = "radar"
    WATERFALL = "waterfall"
    FUNNEL = "funnel"
    STACKED_BAR = "stacked_bar"
    GROUPED_BAR = "grouped_bar"
    COMBINATION = "combination"


class AxisConfig(BaseModel):
    name: Optional[str] = None
    type: str = "category"
    show: bool = True
    show_grid: bool = True
    min: Optional[float] = None
    max: Optional[float] = None


class SeriesConfig(BaseModel):
    name: str
    data: List[Any]
    type: Optional[ChartType] = None
    color: Optional[str] = None
    y_axis_index: int = 0


class ChartConfig(BaseModel):
    type: ChartType
    title: Optional[str] = None
    subtitle: Optional[str] = None
    x_axis: AxisConfig = Field(default_factory=AxisConfig)
    y_axis: AxisConfig = Field(default_factory=AxisConfig)
    series: List[SeriesConfig]
    legend: bool = True
    tooltip: bool = True
    colors: List[str] = Field(default_factory=lambda: [
        "#6366F1", "#06B6D4", "#22C55E", "#F59E0B", "#EF4444",
        "#8B5CF6", "#EC4899", "#14B8A6", "#F97316", "#84CC16"
    ])
    width: Optional[int] = None
    height: Optional[int] = None


class DashboardWidget(BaseModel):
    id: str
    title: str
    chart_type: ChartType
    config: ChartConfig
    dataset_id: str
    x: int = 0
    y: int = 0
    w: int = 6
    h: int = 4


class DashboardBase(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_id: str


class DashboardCreate(DashboardBase):
    pass


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    widgets: Optional[List[DashboardWidget]] = None


class Dashboard(DashboardBase):
    id: str
    widgets: List[DashboardWidget] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardListResponse(BaseModel):
    dashboards: List[Dashboard]
    total: int
    page: int
    page_size: int


class DashboardResponse(BaseModel):
    dashboard: Dashboard