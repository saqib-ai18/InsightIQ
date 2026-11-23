from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
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


class ChartSuggestion(BaseModel):
    chart_type: ChartType
    reason: str
    columns_used: List[str]
    config: ChartConfig


class VisualizationRequest(BaseModel):
    dataset_id: str
    chart_type: Optional[ChartType] = None
    x_column: str
    y_columns: List[str]
    group_by: Optional[str] = None
    filters: Optional[List[Dict[str, Any]]] = None
    aggregation: Optional[str] = None
    limit: Optional[int] = None


class VisualizationResponse(BaseModel):
    chart_config: ChartConfig
    data: List[Dict[str, Any]]
    sql: Optional[str] = None
    suggestions: List[ChartSuggestion] = Field(default_factory=list)


class ChartConfigRequest(BaseModel):
    dataset_id: str
    chart_type: ChartType
    x_column: str
    y_columns: List[str]
    group_by: Optional[str] = None
    filters: Optional[List[Dict[str, Any]]] = None
    aggregation: Optional[str] = None
    limit: Optional[int] = None


class ChartConfigResponse(BaseModel):
    chart_config: Dict[str, Any]
    success: bool


class VisualizationSuggestion(BaseModel):
    chart_type: ChartType
    reason: str
    columns_used: List[str]


class VisualizationSuggestionsResponse(BaseModel):
    suggestions: List[VisualizationSuggestion]