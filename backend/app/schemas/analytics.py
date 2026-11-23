from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AnalyticalOperationType(str, Enum):
    FILTER = "filter"
    SORT = "sort"
    GROUP_BY = "group_by"
    CALCULATE = "calculate"
    RANK = "rank"
    PERCENTAGE = "percentage"
    GROWTH = "growth"
    STATISTICAL_SUMMARY = "statistical_summary"
    CORRELATION = "correlation"
    TREND = "trend"
    OUTLIER = "outlier"
    MISSING_ANALYSIS = "missing_analysis"


class AnalyticalOperation(BaseModel):
    operation: AnalyticalOperationType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class AnalyticalOperationResponse(BaseModel):
    success: bool
    data: Any = None
    row_count: int = 0
    columns: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class SQLQueryRequest(BaseModel):
    query: str


class SQLQueryResponse(BaseModel):
    success: bool
    data: Any = None
    row_count: int = 0
    columns: List[str] = Field(default_factory=list)
    query: str = ""
    error: Optional[str] = None


class CorrelationRequest(BaseModel):
    columns: Optional[List[str]] = None
    method: str = "pearson"


class TrendRequest(BaseModel):
    date_column: str
    value_column: str


class OutlierRequest(BaseModel):
    column: str
    method: str = "iqr"
    threshold: float = 1.5


class MissingAnalysisResponse(BaseModel):
    total_missing: int
    total_cells: int
    missing_percentage: float
    by_column: Dict[str, Dict[str, Any]]
    rows_with_missing: int
    complete_rows: int


class StatisticalSummaryResponse(BaseModel):
    summary: Dict[str, Dict[str, Any]]


class ForecastRequest(BaseModel):
    date_column: str
    value_column: str
    horizon: int = 6
    freq: str = "M"


class AnomalyDetectionRequest(BaseModel):
    columns: Optional[List[str]] = None
    contamination: float = 0.05
    method: str = "isolation_forest"


class SegmentationRequest(BaseModel):
    feature_columns: List[str]
    n_clusters: int = 4