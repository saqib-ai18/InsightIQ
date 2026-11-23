from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DataQualityIssueType(str, Enum):
    MISSING_VALUES = "missing_values"
    DUPLICATE_ROWS = "duplicate_rows"
    INVALID_FORMAT = "invalid_format"
    OUTLIER = "outlier"
    HIGH_CARDINALITY = "high_cardinality"
    CONSTANT_COLUMN = "constant_column"
    TYPE_INCONSISTENCY = "type_inconsistency"


class DataQualityIssue(BaseModel):
    type: DataQualityIssueType
    column: Optional[str] = None
    severity: str = "medium"
    message: str
    count: int = 0
    recommendation: Optional[str] = None


class NumericalStats(BaseModel):
    count: int
    mean: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[float] = None
    std: Optional[float] = None
    variance: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    range: Optional[float] = None
    q25: Optional[float] = None
    q50: Optional[float] = None
    q75: Optional[float] = None
    iqr: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    missing: int = 0
    zeros: int = 0
    negative: int = 0
    positive: int = 0


class CategoricalStats(BaseModel):
    count: int
    unique: int
    top: Optional[str] = None
    freq: Optional[int] = None
    distribution: Dict[str, int] = Field(default_factory=dict)
    missing: int = 0
    cardinality_ratio: float = 0.0


class DateTimeStats(BaseModel):
    count: int
    min: Optional[str] = None
    max: Optional[str] = None
    range_days: Optional[int] = None
    missing: int = 0
    frequency: Optional[str] = None


class ColumnProfile(BaseModel):
    name: str
    type: str
    stats: NumericalStats | CategoricalStats | DateTimeStats | Dict[str, Any]
    quality_issues: List[DataQualityIssue] = Field(default_factory=list)
    sample_values: List[Any] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    dataset_id: str
    dataset_name: str
    row_count: int
    column_count: int
    memory_usage_mb: float
    columns: List[ColumnProfile]
    quality_score: float
    quality_issues: List[DataQualityIssue]
    recommendations: List[str]
    profiled_at: str