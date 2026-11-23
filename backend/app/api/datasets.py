from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import structlog
import io

from app.schemas.dataset import (
    DatasetMetadata, DatasetListResponse, DatasetUpdate,
    UploadResponse, DataPreview
)
from app.services.ingestion.service import ingestion_service
from app.services.profiling.service import profiling_service
from app.api.auth import get_current_active_user, UserResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    sheet_name: Optional[str] = Form(None),
    encoding: str = Form("utf-8"),
    delimiter: str = Form(","),
    has_header: bool = Form(True),
    current_user: UserResponse = Depends(get_current_active_user),
):
    file_content = await file.read()
    file_size = len(file_content)
    filename = file.filename or "unknown"

    valid, error = ingestion_service.validate_file(filename, file_size)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    try:
        file_path = ingestion_service.save_upload(file_content, filename)
        file_type = ingestion_service.detect_file_type(filename)

        df = ingestion_service.read_file(
            file_path, file_type, sheet_name, encoding, delimiter, has_header
        )

        dataset_id = file_path.stem
        metadata = ingestion_service.create_metadata(
            df, filename, file_type, file_size, dataset_id,
            sheet_name, encoding, delimiter
        )

        ingestion_service.save_metadata(metadata, str(file_path))

        logger.info("dataset_uploaded", dataset_id=dataset_id, rows=len(df), columns=len(df.columns))

        return UploadResponse(
            dataset_id=dataset_id,
            status=metadata.status,
            message="Dataset uploaded successfully. Profiling in progress.",
        )
    except Exception as e:
        logger.error("upload_failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_active_user),
):
    datasets = ingestion_service.list_datasets()
    total = len(datasets)
    start = (page - 1) * page_size
    end = start + page_size

    return DatasetListResponse(
        datasets=datasets[start:end],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{dataset_id}", response_model=DatasetMetadata)
async def get_dataset(dataset_id: str, current_user: UserResponse = Depends(get_current_active_user)):
    datasets = ingestion_service.list_datasets()
    for ds in datasets:
        if ds.id == dataset_id:
            return ds
    raise HTTPException(status_code=404, detail="Dataset not found")


@router.get("/{dataset_id}/preview", response_model=DataPreview)
async def preview_dataset(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: UserResponse = Depends(get_current_active_user),
):
    try:
        return ingestion_service.get_preview(dataset_id, page, page_size)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        logger.error("preview_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}/profile")
async def get_profile(dataset_id: str, current_user: UserResponse = Depends(get_current_active_user)):
    try:
        profile = profiling_service.profile_dataset(dataset_id)
        return profile
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        logger.error("profiling_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{dataset_id}", response_model=DatasetMetadata)
async def update_dataset(dataset_id: str, update: DatasetUpdate, current_user: UserResponse = Depends(get_current_active_user)):
    datasets = ingestion_service.list_datasets()
    for ds in datasets:
        if ds.id == dataset_id:
            if update.name:
                ds.name = update.name
                ds.updated_at = ds.updated_at
            return ds
    raise HTTPException(status_code=404, detail="Dataset not found")


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, current_user: UserResponse = Depends(get_current_active_user)):
    success = ingestion_service.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"message": "Dataset deleted successfully"}


@router.get("/{dataset_id}/columns")
async def get_columns(dataset_id: str, current_user: UserResponse = Depends(get_current_active_user)):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
        columns = []
        for col in df.columns:
            col_info = ingestion_service.create_column_info(col, df[col])
            columns.append(col_info)
        return {"columns": columns}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        logger.error("columns_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}/download")
async def download_dataset(
    dataset_id: str,
    format: str = Query("csv", regex="^(csv|json|parquet)$"),
    current_user: UserResponse = Depends(get_current_active_user),
):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
        
        if format == "csv":
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            return StreamingResponse(
                io.BytesIO(csv_buffer.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={dataset_id}.csv"},
            )
        elif format == "json":
            json_buffer = io.StringIO()
            df.to_json(json_buffer, orient="records", date_format="iso")
            json_buffer.seek(0)
            return StreamingResponse(
                io.BytesIO(json_buffer.getvalue().encode()),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={dataset_id}.json"},
            )
        elif format == "parquet":
            parquet_buffer = io.BytesIO()
            df.to_parquet(parquet_buffer, index=False)
            parquet_buffer.seek(0)
            return StreamingResponse(
                parquet_buffer,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={dataset_id}.parquet"},
            )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        logger.error("download_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))