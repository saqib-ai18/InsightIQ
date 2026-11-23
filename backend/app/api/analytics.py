from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import structlog

from app.schemas.analytics import (
    AnalyticalOperation,
    AnalyticalOperationResponse,
    SQLQueryRequest,
    SQLQueryResponse,
    CorrelationRequest,
    TrendRequest,
    OutlierRequest,
    MissingAnalysisResponse,
    StatisticalSummaryResponse,
    ForecastRequest,
    AnomalyDetectionRequest,
    SegmentationRequest,
)
from app.services.analytics.service import analytics_service
from app.services.ingestion.service import ingestion_service

logger = structlog.get_logger()

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/execute", response_model=AnalyticalOperationResponse)
async def execute_operation(dataset_id: str, operation: AnalyticalOperation):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        logger.error("load_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    try:
        result_df = df.copy()

        if operation.operation == "filter":
            result_df = analytics_service.filter_data(result_df, operation.parameters.get("filters", []))
        elif operation.operation == "sort":
            result_df = analytics_service.sort_data(
                result_df,
                operation.parameters.get("columns", []),
                operation.parameters.get("ascending", None),
            )
        elif operation.operation == "group_by":
            result_df = analytics_service.group_by(
                result_df,
                operation.parameters.get("group_columns", []),
                operation.parameters.get("aggregations", {}),
            )
        elif operation.operation == "calculate":
            result_df = analytics_service.calculate_column(
                result_df,
                operation.parameters.get("new_column", ""),
                operation.parameters.get("expression", ""),
            )
        elif operation.operation == "rank":
            result_df = analytics_service.rank_data(
                result_df,
                operation.parameters.get("column", ""),
                operation.parameters.get("ascending", False),
                operation.parameters.get("method", "min"),
            )
        elif operation.operation == "percentage":
            result_df = analytics_service.percentage_of_total(
                result_df,
                operation.parameters.get("column", ""),
                operation.parameters.get("group_by", None),
            )
        elif operation.operation == "growth":
            result_df = analytics_service.growth_rate(
                result_df,
                operation.parameters.get("value_column", ""),
                operation.parameters.get("date_column", ""),
                operation.parameters.get("period", "M"),
            )
        elif operation.operation == "statistical_summary":
            summary = analytics_service.statistical_summary(
                result_df,
                operation.parameters.get("columns", None),
            )
            return AnalyticalOperationResponse(
                success=True,
                data=summary,
                row_count=0,
                columns=[],
            )
        elif operation.operation == "correlation":
            corr = analytics_service.correlation_matrix(
                result_df,
                operation.parameters.get("columns", None),
                operation.parameters.get("method", "pearson"),
            )
            return AnalyticalOperationResponse(
                success=True,
                data=corr,
                row_count=0,
                columns=[],
            )
        elif operation.operation == "trend":
            trend = analytics_service.trend_analysis(
                result_df,
                operation.parameters.get("date_column", ""),
                operation.parameters.get("value_column", ""),
            )
            return AnalyticalOperationResponse(
                success=True,
                data=trend,
                row_count=0,
                columns=[],
            )
        elif operation.operation == "outlier":
            outlier = analytics_service.detect_outliers(
                result_df,
                operation.parameters.get("column", ""),
                operation.parameters.get("method", "iqr"),
                operation.parameters.get("threshold", 1.5),
            )
            return AnalyticalOperationResponse(
                success=True,
                data=outlier,
                row_count=0,
                columns=[],
            )
        elif operation.operation == "missing_analysis":
            missing = analytics_service.missing_analysis(result_df)
            return AnalyticalOperationResponse(
                success=True,
                data=missing,
                row_count=0,
                columns=[],
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {operation.operation}")

        return AnalyticalOperationResponse(
            success=True,
            data=result_df.to_dict(orient="records"),
            row_count=len(result_df),
            columns=result_df.columns.tolist(),
        )

    except Exception as e:
        logger.error("operation_failed", operation=operation.operation, error=str(e))
        return AnalyticalOperationResponse(
            success=False,
            data=None,
            row_count=0,
            columns=[],
            error=str(e),
        )


@router.post("/query", response_model=SQLQueryResponse)
async def execute_sql(dataset_id: str, request: SQLQueryRequest):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        logger.error("load_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    try:
        result_df = analytics_service.execute_sql(df, request.query)
        return SQLQueryResponse(
            success=True,
            data=result_df.to_dict(orient="records"),
            row_count=len(result_df),
            columns=result_df.columns.tolist(),
            query=request.query,
        )
    except Exception as e:
        logger.error("sql_failed", query=request.query, error=str(e))
        return SQLQueryResponse(
            success=False,
            data=None,
            row_count=0,
            columns=[],
            query=request.query,
            error=str(e),
        )


@router.post("/correlation")
async def get_correlation(dataset_id: str, request: CorrelationRequest):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    corr = analytics_service.correlation_matrix(
        df,
        request.columns,
        request.method,
    )
    return corr


@router.post("/trend")
async def get_trend(dataset_id: str, request: TrendRequest):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    trend = analytics_service.trend_analysis(
        df,
        request.date_column,
        request.value_column,
    )
    return trend


@router.post("/outliers")
async def get_outliers(dataset_id: str, request: OutlierRequest):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    outliers = analytics_service.detect_outliers(
        df,
        request.column,
        request.method,
        request.threshold,
    )
    return outliers


@router.get("/missing/{dataset_id}", response_model=MissingAnalysisResponse)
async def get_missing_analysis(dataset_id: str):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    missing = analytics_service.missing_analysis(df)
    return missing


@router.get("/summary/{dataset_id}", response_model=StatisticalSummaryResponse)
async def get_statistical_summary(
    dataset_id: str,
    columns: Optional[List[str]] = Query(None),
):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    summary = analytics_service.statistical_summary(df, columns)
    return {"summary": summary}


@router.post("/forecast")
async def get_forecast(dataset_id: str, request: ForecastRequest):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    forecast = analytics_service.forecast(
        df,
        request.date_column,
        request.value_column,
        request.horizon,
        request.freq,
    )
    return forecast


@router.post("/anomaly-detection")
async def detect_anomalies(dataset_id: str, request: AnomalyDetectionRequest):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    anomalies = analytics_service.anomaly_detection(
        df,
        request.columns,
        request.contamination,
        request.method,
    )
    return anomalies


@router.post("/segmentation")
async def customer_segmentation(dataset_id: str, request: SegmentationRequest):
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    segments = analytics_service.customer_segmentation(
        df,
        request.feature_columns,
        request.n_clusters,
    )
    return segments