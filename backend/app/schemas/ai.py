from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class AnalyticalOperationType(str, Enum):
    FILTER = "filter"
    SORT = "sort"
    GROUP_BY = "group_by"
    AGGREGATE = "aggregate"
    JOIN = "join"
    CALCULATE = "calculate"
    RANK = "rank"
    PERCENTAGE = "percentage"
    GROWTH = "growth"
    STATISTICAL_SUMMARY = "statistical_summary"
    CORRELATION = "correlation"
    TREND = "trend"
    OUTLIER = "outlier"
    MISSING_ANALYSIS = "missing_analysis"
    TIME_SERIES = "time_series"
    FORECAST = "forecast"
    ANOMALY_DETECTION = "anomaly_detection"
    SEGMENTATION = "segmentation"
    RFM = "rfm"
    COHORT = "cohort"


class FilterOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class AggregationFunction(str, Enum):
    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    STD = "std"
    VAR = "var"
    FIRST = "first"
    LAST = "last"


class AnalyticalOperation(BaseModel):
    operation: AnalyticalOperationType
    parameters: Dict[str, Any]
    description: str


class FilterOperation(BaseModel):
    column: str
    operator: FilterOperator
    value: Any


class SortOperation(BaseModel):
    column: str
    order: SortOrder = SortOrder.ASC


class GroupByOperation(BaseModel):
    columns: List[str]
    aggregations: Dict[str, AggregationFunction]


class AggregateOperation(BaseModel):
    columns: Dict[str, AggregationFunction]
    group_by: Optional[List[str]] = None


class CalculateOperation(BaseModel):
    new_column: str
    expression: str


class SQLQuery(BaseModel):
    query: str
    parameters: Optional[List[Any]] = None
    description: str


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AIRequest(BaseModel):
    question: str
    dataset_id: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    context: Optional[Dict[str, Any]] = None


class AIResponse(BaseModel):
    answer: str
    operations: List[AnalyticalOperation] = Field(default_factory=list)
    sql: Optional[str] = None
    data: Optional[Any] = None
    chart_config: Optional[Dict[str, Any]] = None
    citations: List[str] = Field(default_factory=list)
    follow_up_suggestions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    metadata: Optional[Dict[str, Any]] = None