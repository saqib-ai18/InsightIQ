from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import structlog
from starlette.responses import StreamingResponse

from app.schemas.ai import AIRequest, AIResponse
from app.services.ai.service import ai_analyst_service

logger = structlog.get_logger()

router = APIRouter(prefix="/ai", tags=["ai"])


class SQLGenerateRequest(BaseModel):
    question: str
    dataset_id: str


class SQLExecuteRequest(BaseModel):
    sql: str
    dataset_id: str


class SQLResponse(BaseModel):
    sql: str
    explanation: Optional[str] = None
    valid: bool = True
    error: Optional[str] = None


class SQLExecuteResponse(BaseModel):
    success: bool
    data: Optional[list] = None
    row_count: int = 0
    columns: list = []
    sql: str = ""
    error: Optional[str] = None


@router.post("/ask", response_model=AIResponse)
async def ask_question(request: AIRequest):
    try:
        response = await ai_analyst_service.process_question(request)
        return response
    except Exception as e:
        logger.error("ai_ask_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask/stream")
async def ask_question_stream(request: AIRequest):
    async def generate():
        async for chunk in ai_analyst_service.process_question_stream(request):
            yield chunk

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/suggestions")
async def get_suggestions(dataset_id: str = Query(...)):
    try:
        df = None
        try:
            from app.services.ingestion.service import ingestion_service
            df = ingestion_service.load_dataframe(dataset_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dataset not found")

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        date_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

        suggestions = [
            "What are the key insights in this dataset?",
            "Show me a summary of the data",
            "What is the data quality like?",
        ]

        if numeric_cols:
            suggestions.extend([
                f"Show statistics for {numeric_cols[0]}",
                f"Calculate correlation between {numeric_cols[0]} and {numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]}",
                f"Find outliers in {numeric_cols[0]}",
            ])

        if categorical_cols:
            suggestions.extend([
                f"Show distribution of {categorical_cols[0]}",
                f"Group by {categorical_cols[0]} and calculate average",
            ])

        if date_cols and numeric_cols:
            suggestions.extend([
                f"Show trend of {numeric_cols[0]} over time",
                f"Calculate month-over-month growth for {numeric_cols[0]}",
                f"Forecast {numeric_cols[0]} for next 6 months",
            ])

        return {"suggestions": suggestions[:10]}
    except Exception as e:
        logger.error("suggestions_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sql/generate", response_model=SQLResponse)
async def generate_sql(request: SQLGenerateRequest):
    try:
        result = ai_analyst_service.generate_sql_from_nl(request.question, request.dataset_id)
        return SQLResponse(**result)
    except Exception as e:
        logger.error("sql_generate_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sql/execute", response_model=SQLExecuteResponse)
async def execute_sql(request: SQLExecuteRequest):
    try:
        result = ai_analyst_service.validate_and_execute_sql(request.dataset_id, request.sql)
        return SQLExecuteResponse(**result)
    except Exception as e:
        logger.error("sql_execute_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sql/validate")
async def validate_sql(dataset_id: str = Query(...), sql: str = Query(...)):
    try:
        from app.services.ingestion.service import ingestion_service
        from app.services.ai.sql_generator import sql_generator

        df = ingestion_service.load_dataframe(dataset_id)
        validation = sql_generator.validate_sql(sql, df.columns.tolist())
        return validation
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        logger.error("sql_validate_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))