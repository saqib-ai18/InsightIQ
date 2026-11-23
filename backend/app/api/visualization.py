from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional
import structlog
import json
from datetime import datetime
from uuid import uuid4

from app.schemas.visualization import (
    ChartConfigRequest,
    ChartConfigResponse,
    VisualizationSuggestionsResponse,
    VisualizationSuggestion,
    ChartType,
)
from app.services.visualization.service import visualization_service
from app.core.database import get_db_session
from app.models.database import ChartModel

logger = structlog.get_logger()

router = APIRouter(prefix="/visualizations", tags=["visualizations"])


@router.post("/suggest", response_model=VisualizationSuggestionsResponse)
async def suggest_charts(dataset_id: str = Query(...)):
    try:
        suggestions = visualization_service.suggest_charts(dataset_id)
        validated_suggestions = [
            VisualizationSuggestion(
                chart_type=ChartType(s["chart_type"]),
                reason=s["reason"],
                columns_used=s["columns_used"],
            )
            for s in suggestions
        ]
        return VisualizationSuggestionsResponse(suggestions=validated_suggestions)
    except Exception as e:
        logger.error("suggest_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=ChartConfigResponse)
async def generate_chart(request: ChartConfigRequest):
    try:
        data = visualization_service.generate_chart_data(
            dataset_id=request.dataset_id,
            chart_type=request.chart_type,
            x_column=request.x_column,
            y_columns=request.y_columns,
            group_by=request.group_by,
            filters=request.filters,
            aggregation=request.aggregation,
            limit=request.limit,
        )
        return ChartConfigResponse(
            chart_config=data,
            success=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("generate_failed", dataset_id=request.dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


class ChartDataRequest(BaseModel):
    dataset_id: str
    chart_type: str
    x_column: str = ""
    y_columns: List[str] = []
    group_by: Optional[str] = None
    filters: Optional[List[dict]] = None
    aggregation: Optional[str] = None
    limit: Optional[int] = None


@router.post("/data")
async def get_chart_data(request: ChartDataRequest):
    try:
        data = visualization_service.generate_chart_data(
            dataset_id=request.dataset_id,
            chart_type=request.chart_type,
            x_column=request.x_column,
            y_columns=request.y_columns,
            group_by=request.group_by,
            filters=request.filters,
            aggregation=request.aggregation,
            limit=request.limit,
        )
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("data_failed", dataset_id=request.dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def save_chart(
    dataset_id: str = Body(...),
    title: str = Body(...),
    chart_type: str = Body(...),
    config: dict = Body(...),
):
    try:
        chart_id = str(uuid4())
        with get_db_session() as db:
            chart = ChartModel(
                id=chart_id,
                title=title,
                chart_type=chart_type,
                config=config,
                dataset_id=dataset_id,
            )
            db.add(chart)
            db.commit()
        return {"id": chart_id, "message": "Chart saved successfully"}
    except Exception as e:
        logger.error("save_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_charts(dataset_id: str = Query(...)):
    with get_db_session() as db:
        charts = db.query(ChartModel).filter(ChartModel.dataset_id == dataset_id).order_by(ChartModel.created_at.desc()).all()
        return {"charts": [
            {
                "id": c.id,
                "title": c.title,
                "chart_type": c.chart_type,
                "config": c.config,
                "dataset_id": c.dataset_id,
                "created_at": c.created_at.isoformat() if c.created_at else "",
            }
            for c in charts
        ]}


@router.delete("/{chart_id}")
async def delete_chart(chart_id: str):
    with get_db_session() as db:
        chart = db.query(ChartModel).filter(ChartModel.id == chart_id).first()
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found")
        db.delete(chart)
        db.commit()
    return {"message": "Chart deleted successfully"}