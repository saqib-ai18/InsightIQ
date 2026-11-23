from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FileType(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
    JSON = "json"
    PARQUET = "parquet"


class ColumnType(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    CATEGORY = "category"


class DatasetStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PROFILING = "profiling"
    READY = "ready"
    ERROR = "error"


class ColumnInfo(BaseModel):
    name: str
    type: ColumnType
    nullable: bool = True
    unique: bool = False
    sample_values: List[Any] = Field(default_factory=list)
    stats: Optional[Dict[str, Any]] = None


class DatasetMetadata(BaseModel):
    id: str
    name: str
    original_filename: str
    file_type: FileType
    file_size_bytes: int
    row_count: int
    column_count: int
    columns: List[ColumnInfo]
    missing_values: int = 0
    duplicate_rows: int = 0
    quality_score: float = 100.0
    status: DatasetStatus = DatasetStatus.READY
    created_at: datetime
    updated_at: datetime
    sheet_name: Optional[str] = None
    encoding: Optional[str] = None
    delimiter: Optional[str] = None


class DatasetCreate(BaseModel):
    name: Optional[str] = None
    sheet_name: Optional[str] = None
    encoding: Optional[str] = "utf-8"
    delimiter: Optional[str] = ","
    has_header: bool = True


class DatasetUpdate(BaseModel):
    name: Optional[str] = None


class DatasetListResponse(BaseModel):
    datasets: List[DatasetMetadata]
    total: int
    page: int
    page_size: int


class UploadResponse(BaseModel):
    dataset_id: str
    status: DatasetStatus
    message: str


class DataPreview(BaseModel):
    columns: List[ColumnInfo]
    rows: List[List[Any]]
    total_rows: int
    page: int
    page_size: int