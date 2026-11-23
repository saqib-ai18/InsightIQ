import json
import time
from typing import Any, Dict, List, Optional
import structlog

from app.core.config import get_settings
from app.schemas.ai import (
    AIRequest,
    AIResponse,
    AnalyticalOperation,
    AnalyticalOperationType,
)
from app.services.ai.providers import get_llm_provider, LLMProvider
from app.services.ai.tools import (
    ANALYTICAL_TOOLS,
    execute_tool,
)
from app.services.ai.sql_generator import sql_generator
from app.services.ingestion.service import ingestion_service
from app.services.ai.rate_limiter import RateLimiter

logger = structlog.get_logger()


SYSTEM_PROMPT = """You are an expert AI Data Analyst for InsightIQ. Your role is to help users analyze their datasets through natural language.

You have access to a powerful analytical engine that can perform:
- Filtering, sorting, grouping, and aggregation
- Statistical summaries and correlations
- Trend analysis and growth calculations
- Outlier detection and missing value analysis
- Custom column calculations
- SQL queries via DuckDB
- Ranking and percentage calculations

Guidelines:
1. ALWAYS use the available tools to perform actual analysis - never guess or fabricate numbers
2. When users ask questions, identify the relevant dataset columns and determine the appropriate analytical operations
3. Execute operations through the tool interface, then explain the results clearly
4. Provide methodology explanations when appropriate
5. Suggest visualizations when results would benefit from charts
6. Ask clarifying questions if the request is ambiguous
7. Maintain conversation context for follow-up questions
8. Be honest about limitations - if data is insufficient, say so

Response format:
- Provide clear, actionable insights
- Include key numbers and statistics
- Explain methodology briefly
- Suggest follow-up analyses
- Recommend chart types when appropriate"""


class AIAnalystService:
    def __init__(self):
        self.settings = get_settings()
        self.provider: LLMProvider = get_llm_provider()
        self.max_tool_iterations = 5
        self.rate_limiter = RateLimiter()

    async def process_question(self, request: AIRequest) -> AIResponse:
        # Check rate limit
        user_id = getattr(request, 'user_id', 'anonymous')
        allowed, error_msg = self.rate_limiter.check_rate_limit(user_id)
        if not allowed:
            return AIResponse(
                answer=error_msg or "Rate limit exceeded. Please try again later.",
                operations=[],
                follow_up_suggestions=["Wait a moment and try again"],
            )
        try:
            df = ingestion_service.load_dataframe(request.dataset_id)
        except FileNotFoundError:
            return AIResponse(
                answer="Dataset not found. Please upload a dataset first.",
                operations=[],
                follow_up_suggestions=["Upload a dataset to begin analysis"],
            )
        except Exception as e:
            logger.error("load_dataset_failed", dataset_id=request.dataset_id, error=str(e))
            return AIResponse(
                answer=f"Failed to load dataset: {str(e)}",
                operations=[],
            )

        dataset_context = self._build_dataset_context(df)
        messages = self._build_messages(request, dataset_context)

        operations_performed = []
        all_tool_results = []

        for iteration in range(self.max_tool_iterations):
            response = await self.provider.chat_completion(
                messages=messages,
                tools=ANALYTICAL_TOOLS,
                tool_choice="auto",
                temperature=self.settings.LLM_TEMPERATURE,
                max_tokens=self.settings.LLM_MAX_TOKENS,
            )

            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])

            if tool_calls:
                for tool_call_data in tool_calls:
                    tool_call = self._parse_tool_call(tool_call_data)
                    logger.info("tool_called", tool=tool_call.name, args=tool_call.arguments)

                    result = await execute_tool(request.dataset_id, tool_call)
                    all_tool_results.append((tool_call, result))

                    if result.success:
                        operation = self._tool_to_operation(tool_call.name, tool_call.arguments)
                        if operation:
                            operations_performed.append(operation)

                        messages.append({
                            "role": "assistant",
                            "content": content,
                            "tool_calls": [tool_call_data],
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_data["id"],
                            "content": json.dumps(result.data) if result.data else "Operation completed",
                        })
                    else:
                        messages.append({
                            "role": "assistant",
                            "content": content,
                            "tool_calls": [tool_call_data],
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_data["id"],
                            "content": f"Error: {result.error}",
                        })

                continue
            else:
                final_answer = content
                break
        else:
            final_answer = "I've performed the analysis but reached the maximum number of tool iterations. Here's what I found so far."

        follow_ups = self._generate_follow_ups(request.question, operations_performed, df)
        chart_config = self._suggest_chart(operations_performed, all_tool_results)
        citations = self._generate_citations(operations_performed, all_tool_results)

        return AIResponse(
            answer=final_answer,
            operations=operations_performed,
            data=all_tool_results[-1][1].data if all_tool_results else None,
            chart_config=chart_config,
            citations=citations,
            follow_up_suggestions=follow_ups,
            metadata={
                "dataset_rows": len(df),
                "dataset_columns": len(df.columns),
                "operations_count": len(operations_performed),
            },
        )

    async def process_question_stream(
        self,
        request: AIRequest,
    ):
        # Check rate limit
        user_id = getattr(request, 'user_id', 'anonymous')
        allowed, error_msg = self.rate_limiter.check_rate_limit(user_id)
        if not allowed:
            yield "data: " + json.dumps({"type": "error", "error": error_msg or "Rate limit exceeded"}) + "\n\n"
            return

        try:
            df = ingestion_service.load_dataframe(request.dataset_id)
        except FileNotFoundError:
            yield "data: " + json.dumps({"error": "Dataset not found"}) + "\n\n"
            return
        except Exception as e:
            yield "data: " + json.dumps({"error": f"Failed to load dataset: {str(e)}"}) + "\n\n"
            return

        dataset_context = self._build_dataset_context(df)
        messages = self._build_messages(request, dataset_context)

        operations_performed = []

        for iteration in range(self.max_tool_iterations):
            response = await self.provider.chat_completion(
                messages=messages,
                tools=ANALYTICAL_TOOLS,
                tool_choice="auto",
                temperature=self.settings.LLM_TEMPERATURE,
                max_tokens=self.settings.LLM_MAX_TOKENS,
            )

            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])

            if content:
                yield "data: " + json.dumps({"type": "content", "content": content}) + "\n\n"

            if tool_calls:
                for tool_call_data in tool_calls:
                    tool_call = self._parse_tool_call(tool_call_data)
                    yield "data: " + json.dumps({"type": "tool_start", "tool": tool_call.name}) + "\n\n"

                    result = await execute_tool(request.dataset_id, tool_call)

                    if result.success:
                        operation = self._tool_to_operation(tool_call.name, tool_call.arguments)
                        if operation:
                            operations_performed.append(operation)

                        messages.append({
                            "role": "assistant",
                            "content": content,
                            "tool_calls": [tool_call_data],
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_data["id"],
                            "content": json.dumps(result.data) if result.data else "Operation completed",
                        })
                        yield "data: " + json.dumps({"type": "tool_result", "tool": tool_call.name, "success": True}) + "\n\n"
                    else:
                        messages.append({
                            "role": "assistant",
                            "content": content,
                            "tool_calls": [tool_call_data],
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_data["id"],
                            "content": f"Error: {result.error}",
                        })
                        yield "data: " + json.dumps({"type": "tool_result", "tool": tool_call.name, "success": False, "error": result.error}) + "\n\n"

                continue
            else:
                break
        else:
            yield "data: " + json.dumps({"type": "content", "content": "Maximum iterations reached."}) + "\n\n"

        follow_ups = self._generate_follow_ups(request.question, operations_performed, df)
        yield "data: " + json.dumps({"type": "complete", "follow_ups": follow_ups}) + "\n\n"

    def _build_dataset_context(self, df) -> str:
        cols_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            nulls = int(df[col].isna().sum())
            unique = int(df[col].nunique())
            sample = df[col].dropna().head(3).tolist()
            cols_info.append(f"- {col} ({dtype}): {unique} unique, {nulls} nulls, sample: {sample}")

        return f"""Dataset: {len(df)} rows × {len(df.columns)} columns
Columns:
{chr(10).join(cols_info)}"""

    def _build_messages(self, request: AIRequest, dataset_context: str) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Active Dataset Context:\n{dataset_context}"},
        ]

        if request.conversation_history:
            for msg in request.conversation_history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": request.question})
        return messages

    def _parse_tool_call(self, tool_call_data: Dict) -> Any:
        class ToolCall:
            def __init__(self, name: str, arguments: Dict):
                self.name = name
                self.arguments = arguments

        return ToolCall(
            name=tool_call_data["name"],
            arguments=tool_call_data["arguments"],
        )

    def _tool_to_operation(self, tool_name: str, arguments: Dict) -> Optional[AnalyticalOperation]:
        tool_to_operation = {
            "filter_data": AnalyticalOperationType.FILTER,
            "sort_data": AnalyticalOperationType.SORT,
            "group_by": AnalyticalOperationType.GROUP_BY,
            "calculate_column": AnalyticalOperationType.CALCULATE,
            "rank_data": AnalyticalOperationType.RANK,
            "percentage_of_total": AnalyticalOperationType.PERCENTAGE,
            "growth_rate": AnalyticalOperationType.GROWTH,
            "statistical_summary": AnalyticalOperationType.STATISTICAL_SUMMARY,
            "correlation_matrix": AnalyticalOperationType.CORRELATION,
            "trend_analysis": AnalyticalOperationType.TREND,
            "detect_outliers": AnalyticalOperationType.OUTLIER,
            "missing_analysis": AnalyticalOperationType.MISSING_ANALYSIS,
            "execute_sql": AnalyticalOperationType.TREND,
        }

        op_type = tool_to_operation.get(tool_name)
        if not op_type:
            return None

        return AnalyticalOperation(operation=op_type, parameters=arguments, description=f"Executed {tool_name}")

    def generate_sql_from_nl(
        self,
        question: str,
        dataset_id: str,
    ) -> Dict[str, Any]:
        try:
            df = ingestion_service.load_dataframe(dataset_id)
        except FileNotFoundError:
            return {"sql": "", "error": "Dataset not found", "valid": False}
        except Exception as e:
            logger.error("load_dataset_failed", dataset_id=dataset_id, error=str(e))
            return {"sql": "", "error": str(e), "valid": False}

        return sql_generator.generate_sql_from_nl(question, df.columns.tolist(), df)

    def validate_and_execute_sql(self, dataset_id: str, sql: str) -> Dict[str, Any]:
        try:
            df = ingestion_service.load_dataframe(dataset_id)
        except FileNotFoundError:
            return {"success": False, "error": "Dataset not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        validation = sql_generator.validate_sql(sql, df.columns.tolist())
        if not validation["valid"]:
            return {"success": False, "error": validation["error"], "sql": sql}

        try:
            from app.services.analytics.service import analytics_service
            result_df = analytics_service.execute_sql(df, sql)
            return {
                "success": True,
                "data": result_df.to_dict(orient="records"),
                "row_count": len(result_df),
                "columns": result_df.columns.tolist(),
                "sql": validation["sanitized_sql"],
            }
        except Exception as e:
            logger.error("sql_execution_failed", sql=sql, error=str(e))
            return {"success": False, "error": str(e), "sql": sql}

    def _generate_follow_ups(
        self,
        question: str,
        operations: List[AnalyticalOperation],
        df,
    ) -> List[str]:
        suggestions = []

        if any(op.operation == AnalyticalOperationType.GROUP_BY for op in operations):
            suggestions.append("Show this as a bar chart")
            suggestions.append("Calculate percentages for each group")

        if any(op.operation == AnalyticalOperationType.TREND for op in operations):
            suggestions.append("Forecast the next 6 months")
            suggestions.append("Show confidence intervals")

        if any(op.operation == AnalyticalOperationType.CORRELATION for op in operations):
            suggestions.append("Create a correlation heatmap")
            suggestions.append("Analyze causation vs correlation")

        if not suggestions:
            suggestions = [
                "What are the key trends in this data?",
                "Show me the top 5 categories",
                "Calculate month-over-month growth",
                "Identify any outliers",
                "Generate an executive summary",
            ]

        return suggestions[:4]

    def _suggest_chart(
        self,
        operations: List[AnalyticalOperation],
        tool_results: List[tuple],
    ) -> Optional[Dict[str, Any]]:
        if not tool_results:
            return None

        last_result = tool_results[-1][1]
        if not last_result.data:
            return None

        data = last_result.data
        if isinstance(data, list) and len(data) > 0:
            first_row = data[0]
            if isinstance(first_row, dict):
                keys = list(first_row.keys())
                if len(keys) >= 2:
                    return {
                        "type": "bar",
                        "title": "Analysis Results",
                        "x_axis": {"name": keys[0], "type": "category"},
                        "y_axis": {"name": keys[1], "type": "value"},
                        "series": [{"name": keys[1], "data": [row.get(keys[1]) for row in data[:20]]}],
                    }

        return None

    def _generate_citations(
        self,
        operations: List[AnalyticalOperation],
        tool_results: List[tuple],
    ) -> List[str]:
        citations = []
        for op, (tool_call, result) in zip(operations, tool_results):
            if result.success:
                citations.append(f"{op.description} - {result.metadata.get('row_count', 0)} rows returned")
        return citations


ai_analyst_service = AIAnalystService()