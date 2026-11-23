import uuid
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List
import structlog
import json
import io

from app.core.config import get_settings
from app.core.database import get_db_session, init_db
from app.models.database import DatasetModel
from app.schemas.dataset import (
    DatasetMetadata, ColumnInfo, ColumnType, FileType, DatasetStatus, DataPreview
)
from app.services.storage.r2_service import r2_storage_service

logger = structlog.get_logger()


class IngestionService:
    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        init_db()

    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        ext = filename.lower().split('.')[-1]
        allowed = self.settings.ALLOWED_EXTENSIONS.split(',')

        if ext not in allowed:
            return False, f"File type .{ext} not allowed. Allowed: {', '.join(allowed)}"

        max_size = self.settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            return False, f"File size {file_size / (1024*1024):.1f}MB exceeds limit of {self.settings.MAX_FILE_SIZE_MB}MB"

        return True, ""

    def detect_file_type(self, filename: str) -> FileType:
        ext = filename.lower().split('.')[-1]
        mapping = {
            'csv': FileType.CSV,
            'xlsx': FileType.XLSX,
            'xls': FileType.XLS,
            'json': FileType.JSON,
            'parquet': FileType.PARQUET,
        }
        return mapping.get(ext, FileType.CSV)

    def read_file(
        self,
        file_path: Path,
        file_type: FileType,
        sheet_name: Optional[str] = None,
        encoding: str = "utf-8",
        delimiter: str = ",",
        has_header: bool = True,
    ) -> pd.DataFrame:
        try:
            if file_type == FileType.CSV:
                return pd.read_csv(
                    file_path,
                    encoding=encoding,
                    delimiter=delimiter,
                    header=0 if has_header else None,
                    low_memory=False,
                )
            elif file_type in (FileType.XLSX, FileType.XLS):
                return pd.read_excel(
                    file_path,
                    sheet_name=sheet_name or 0,
                    header=0 if has_header else None,
                )
            elif file_type == FileType.JSON:
                return pd.read_json(file_path)
            elif file_type == FileType.PARQUET:
                return pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error("file_read_failed", file_path=str(file_path), error=str(e))
            raise

    def infer_column_type(self, series: pd.Series) -> ColumnType:
        if pd.api.types.is_integer_dtype(series):
            return ColumnType.INTEGER
        elif pd.api.types.is_float_dtype(series):
            return ColumnType.FLOAT
        elif pd.api.types.is_bool_dtype(series):
            return ColumnType.BOOLEAN
        elif pd.api.types.is_datetime64_any_dtype(series):
            return ColumnType.DATETIME
        elif pd.api.types.is_object_dtype(series):
            try:
                pd.to_datetime(series.dropna().iloc[0])
                return ColumnType.DATETIME
            except (ValueError, TypeError, IndexError):
                unique_ratio = series.nunique() / len(series) if len(series) > 0 else 0
                if unique_ratio < 0.05 and series.nunique() < 50:
                    return ColumnType.CATEGORY
                return ColumnType.STRING
        return ColumnType.STRING

    def create_column_info(self, name: str, series: pd.Series) -> ColumnInfo:
        col_type = self.infer_column_type(series)
        nullable = series.isnull().any()
        unique = series.nunique() == len(series)
        sample_values = series.dropna().head(5).tolist()

        return ColumnInfo(
            name=name,
            type=col_type,
            nullable=nullable,
            unique=unique,
            sample_values=sample_values,
        )

    def create_metadata(
        self,
        df: pd.DataFrame,
        filename: str,
        file_type: FileType,
        file_size: int,
        dataset_id: str,
        sheet_name: Optional[str] = None,
        encoding: Optional[str] = None,
        delimiter: Optional[str] = None,
    ) -> DatasetMetadata:
        from datetime import datetime

        columns = [self.create_column_info(col, df[col]) for col in df.columns]
        missing_values = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        quality_score = 100.0
        if missing_values > 0:
            quality_score -= min(30, (missing_values / (len(df) * len(df.columns))) * 100)
        if duplicate_rows > 0:
            quality_score -= min(20, (duplicate_rows / len(df)) * 100)
        quality_score = max(0, quality_score)

        return DatasetMetadata(
            id=dataset_id,
            name=filename,
            original_filename=filename,
            file_type=file_type,
            file_size_bytes=file_size,
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns,
            missing_values=missing_values,
            duplicate_rows=duplicate_rows,
            quality_score=round(quality_score, 1),
            status=DatasetStatus.READY,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            sheet_name=sheet_name,
            encoding=encoding,
            delimiter=delimiter,
        )

    def save_upload(self, file_content: bytes, filename: str) -> str:
        dataset_id = str(uuid.uuid4())
        ext = filename.lower().split('.')[-1]
        object_key = f"datasets/{dataset_id}.{ext}"

        if r2_storage_service.is_enabled:
            content_type = self._get_content_type(ext)
            if r2_storage_service.upload_file(file_content, object_key=object_key, content_type=content_type):
                return object_key
            logger.warning("R2 upload failed, falling back to local storage")

        # Fallback to local storage
        dataset_id = str(uuid.uuid4())
        ext = filename.lower().split('.')[-1]
        saved_filename = f"{dataset_id}.{ext}"
        file_path = self.upload_dir / saved_filename
        file_path.write_bytes(file_content)
        return str(file_path)

    def _get_content_type(self, ext: str) -> str:
        content_types = {
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            'json': 'application/json',
            'parquet': 'application/octet-stream',
        }
        return content_types.get(ext, 'application/octet-stream')

    def load_dataframe(self, dataset_id: str) -> pd.DataFrame:
        file_path_or_key = self._get_file_path(dataset_id)
        if file_path_or_key is None:
            raise FileNotFoundError(f"Dataset {dataset_id} not found")

        file_type = self.detect_file_type(file_path_or_key)
        
        if r2_storage_service.is_enabled and file_path_or_key.startswith("datasets/"):
            file_content = r2_storage_service.download_file(file_path_or_key)
            if file_content:
                file_buffer = io.BytesIO(file_content)
                return self.read_file_from_buffer(file_buffer, file_type)
            logger.warning("R2 download failed, falling back to local storage")

        # Fallback to local storage
        file_path = Path(file_path_or_key)
        return self.read_file(file_path, file_type)

    def _get_file_path(self, dataset_id: str) -> Optional[str]:
        # First check R2
        if r2_storage_service.is_enabled:
            # We need to find the object key - check common extensions
            for ext in ['csv', 'xlsx', 'xls', 'json', 'parquet']:
                object_key = f"datasets/{dataset_id}.{ext}"
                if r2_storage_service.file_exists(object_key):
                    return object_key

        # Fallback to local storage
        files = list(self.upload_dir.glob(f"{dataset_id}.*"))
        if files:
            return str(files[0])
        return None

    def read_file_from_buffer(self, buffer: io.BytesIO, file_type: FileType) -> pd.DataFrame:
        try:
            if file_type == FileType.CSV:
                return pd.read_csv(buffer, low_memory=False)
            elif file_type in (FileType.XLSX, FileType.XLS):
                return pd.read_excel(buffer)
            elif file_type == FileType.JSON:
                return pd.read_json(buffer)
            elif file_type == FileType.PARQUET:
                return pd.read_parquet(buffer)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error("file_read_from_buffer_failed", error=str(e))
            raise

    def get_preview(
        self,
        dataset_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> DataPreview:
        df = self.load_dataframe(dataset_id)
        columns = [self.create_column_info(col, df[col]) for col in df.columns]

        start = (page - 1) * page_size
        end = start + page_size
        preview_df = df.iloc[start:end]

        return DataPreview(
            columns=columns,
            rows=preview_df.values.tolist(),
            total_rows=len(df),
            page=page,
            page_size=page_size,
        )

    def list_datasets(self) -> List[DatasetMetadata]:
        datasets = []
        with get_db_session() as db:
            db_datasets = db.query(DatasetModel).order_by(DatasetModel.created_at.desc()).all()
            for ds in db_datasets:
                metadata = self._model_to_metadata(ds)
                datasets.append(metadata)
        return datasets

    def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        with get_db_session() as db:
            ds = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
            if ds:
                return self._model_to_metadata(ds)
        return None

    def _model_to_metadata(self, model: DatasetModel) -> DatasetMetadata:
        columns = []
        if model.columns:
            for col_data in model.columns:
                columns.append(ColumnInfo(**col_data))
        
        return DatasetMetadata(
            id=model.id,
            name=model.name,
            original_filename=model.original_filename,
            file_type=FileType(model.file_type),
            file_size_bytes=model.file_size_bytes,
            row_count=model.row_count,
            column_count=model.column_count,
            columns=columns,
            missing_values=model.missing_values,
            duplicate_rows=model.duplicate_rows,
            quality_score=model.quality_score,
            status=DatasetStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            sheet_name=model.sheet_name,
            encoding=model.encoding,
            delimiter=model.delimiter,
        )

    def save_metadata(self, metadata: DatasetMetadata, file_path: str):
        with get_db_session() as db:
            db_dataset = DatasetModel(
                id=metadata.id,
                name=metadata.name,
                original_filename=metadata.original_filename,
                file_type=metadata.file_type.value,
                file_size_bytes=metadata.file_size_bytes,
                row_count=metadata.row_count,
                column_count=metadata.column_count,
                columns=[col.model_dump() for col in metadata.columns],
                missing_values=metadata.missing_values,
                duplicate_rows=metadata.duplicate_rows,
                quality_score=metadata.quality_score,
                status=metadata.status.value,
                sheet_name=metadata.sheet_name,
                encoding=metadata.encoding,
                delimiter=metadata.delimiter,
                file_path=file_path,
            )
            db.merge(db_dataset)
            db.commit()

    def delete_dataset(self, dataset_id: str) -> bool:
        deleted = False

        # Delete from R2 if enabled
        if r2_storage_service.is_enabled:
            for ext in ['csv', 'xlsx', 'xls', 'json', 'parquet']:
                object_key = f"datasets/{dataset_id}.{ext}"
                if r2_storage_service.file_exists(object_key):
                    r2_storage_service.delete_file(object_key)
                    deleted = True

        # Delete from local storage
        files = list(self.upload_dir.glob(f"{dataset_id}.*"))
        for f in files:
            f.unlink()
            deleted = True
        
        with get_db_session() as db:
            db.query(DatasetModel).filter(DatasetModel.id == dataset_id).delete()
            db.commit()
        
        return deleted


ingestion_service = IngestionService()