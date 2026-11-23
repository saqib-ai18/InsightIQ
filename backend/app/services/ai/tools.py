import structlog

from app.services.analytics.service import analytics_service
from app.services.ingestion.service import ingestion_service
from app.schemas.ai import ToolCall, ToolResult, AnalyticalOperation, AnalyticalOperationType

logger = structlog.get_logger()


ANALYTICAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "filter_data",
            "description": "Filter dataset rows based on conditions",
            "parameters": {
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "column": {"type": "string", "description": "Column name to filter"},
                                "operator": {
                                    "type": "string",
                                    "enum": ["eq", "neq", "gt", "gte", "lt", "lte", "in", "not_in", "contains", "not_contains", "starts_with", "ends_with", "is_null", "is_not_null", "between"],
                                    "description": "Comparison operator"
                                },
                                "value": {"description": "Value to compare against"},
                            },
                            "required": ["column", "operator"],
                        },
                    },
                },
                "required": ["filters"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sort_data",
            "description": "Sort dataset by one or more columns",
            "parameters": {
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "Columns to sort by"},
                    "ascending": {"type": "array", "items": {"type": "boolean"}, "description": "Sort direction for each column"},
                },
                "required": ["columns"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "group_by",
            "description": "Group data and aggregate",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_columns": {"type": "array", "items": {"type": "string"}, "description": "Columns to group by"},
                    "aggregations": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "string",
                            "enum": ["sum", "mean", "median", "min", "max", "count", "count_distinct", "std", "var", "first", "last"],
                        },
                        "description": "Column to aggregation function mapping",
                    },
                },
                "required": ["group_columns", "aggregations"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_column",
            "description": "Create a new calculated column using an expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_column": {"type": "string", "description": "Name of the new column"},
                    "expression": {"type": "string", "description": "Expression using existing column names (e.g., 'revenue - cost')"},
                },
                "required": ["new_column", "expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rank_data",
            "description": "Rank data by a column",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "Column to rank by"},
                    "ascending": {"type": "boolean", "description": "Sort direction", "default": False},
                    "method": {"type": "string", "enum": ["min", "max", "average", "dense", "first"], "default": "min"},
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "percentage_of_total",
            "description": "Calculate percentage of total for a column",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "Column to calculate percentage for"},
                    "group_by": {"type": "array", "items": {"type": "string"}, "description": "Optional grouping columns"},
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "growth_rate",
            "description": "Calculate period-over-period growth rate",
            "parameters": {
                "type": "object",
                "properties": {
                    "value_column": {"type": "string", "description": "Column with values"},
                    "date_column": {"type": "string", "description": "Column with dates"},
                    "period": {"type": "string", "enum": ["D", "W", "M", "Q", "Y"], "default": "M"},
                },
                "required": ["value_column", "date_column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "statistical_summary",
            "description": "Get statistical summary of numerical columns",
            "parameters": {
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "Columns to summarize (default: all numeric)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "correlation_matrix",
            "description": "Calculate correlation matrix between numerical columns",
            "parameters": {
                "type": "object",
                "properties": {
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "Columns to correlate (default: all numeric)"},
                    "method": {"type": "string", "enum": ["pearson", "spearman", "kendall"], "default": "pearson"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trend_analysis",
            "description": "Analyze trend over time using linear regression",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_column": {"type": "string", "description": "Date column"},
                    "value_column": {"type": "string", "description": "Value column"},
                },
                "required": ["date_column", "value_column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_outliers",
            "description": "Detect outliers in a column",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "description": "Column to check"},
                    "method": {"type": "string", "enum": ["iqr", "zscore", "modified_zscore"], "default": "iqr"},
                    "threshold": {"type": "number", "default": 1.5},
                },
                "required": ["column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "missing_analysis",
            "description": "Analyze missing values in the dataset",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Execute a read-only SQL query on the dataset using DuckDB",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query (SELECT only)"},
                },
                "required": ["query"],
            },
        },
    },
]


async def execute_tool(dataset_id: str, tool_call: ToolCall) -> ToolResult:
    try:
        df = ingestion_service.load_dataframe(dataset_id)
    except FileNotFoundError:
        return ToolResult(success=False, error="Dataset not found")
    except Exception as e:
        logger.error("load_dataset_failed", dataset_id=dataset_id, error=str(e))
        return ToolResult(success=False, error=str(e))

    try:
        name = tool_call.name
        args = tool_call.arguments

        if name == "filter_data":
            result_df = analytics_service.filter_data(df, args.get("filters", []))
            return ToolResult(
                success=True,
                data=result_df.to_dict(orient="records"),
                metadata={"row_count": len(result_df), "columns": result_df.columns.tolist()},
            )

        elif name == "sort_data":
            result_df = analytics_service.sort_data(df, args.get("columns", []), args.get("ascending"))
            return ToolResult(
                success=True,
                data=result_df.to_dict(orient="records"),
                metadata={"row_count": len(result_df), "columns": result_df.columns.tolist()},
            )

        elif name == "group_by":
            result_df = analytics_service.group_by(
                df, args.get("group_columns", []), args.get("aggregations", {})
            )
            return ToolResult(
                success=True,
                data=result_df.to_dict(orient="records"),
                metadata={"row_count": len(result_df), "columns": result_df.columns.tolist()},
            )

        elif name == "calculate_column":
            result_df = analytics_service.calculate_column(df, args.get("new_column", ""), args.get("expression", ""))
            return ToolResult(
                success=True,
                data=result_df.to_dict(orient="records"),
                metadata={"row_count": len(result_df), "columns": result_df.columns.tolist()},
            )

        elif name == "rank_data":
            result_df = analytics_service.rank_data(
                df, args.get("column", ""), args.get("ascending", False), args.get("method", "min")
            )
            return ToolResult(
                success=True,
                data=result_df.to_dict(orient="records"),
                metadata={"row_count": len(result_df), "columns": result_df.columns.tolist()},
            )

        elif name == "percentage_of_total":
            result_df = analytics_service.percentage_of_total(df, args.get("column", ""), args.get("group_by"))
            return ToolResult(
                success=True,
                data=result_df.to_dict(orient="records"),
                metadata={"row_count": len(result_df), "columns": result_df.columns.tolist()},
            )

        elif name == "growth_rate":
            result_df = analytics_service.growth_rate(
                df, args.get("value_column", ""), args.get("date_column", ""), args.get("period", "M")
            )
            return ToolResult(
                success=True,
                data=result_df.to_dict(orient="records"),
                metadata={"row_count": len(result_df), "columns": result_df.columns.tolist()},
            )

        elif name == "statistical_summary":
            summary = analytics_service.statistical_summary(df, args.get("columns"))
            return ToolResult(success=True, data=summary, metadata={})

        elif name == "correlation_matrix":
            corr = analytics_service.correlation_matrix(df, args.get("columns"), args.get("method", "pearson"))
            return ToolResult(success=True, data=corr, metadata={})

        elif name == "trend_analysis":
            trend = analytics_service.trend_analysis(df, args.get("date_column", ""), args.get("value_column", ""))
            return ToolResult(success=True, data=trend, metadata={})

        elif name == "detect_outliers":
            outliers = analytics_service.detect_outliers(
                df, args.get("column", ""), args.get("method", "iqr"), args.get("threshold", 1.5)
            )
            return ToolResult(success=True, data=outliers, metadata={})

        elif name == "missing_analysis":
            missing = analytics_service.missing_analysis(df)
            return ToolResult(success=True, data=missing, metadata={})

        elif name == "execute_sql":
            result_df = analytics_service.execute_sql(df, args.get("query", ""))
            return ToolResult(
                success=True,
                data=result_df.to_dict(orient="records"),
                metadata={"row_count": len(result_df), "columns": result_df.columns.tolist()},
            )

        else:
            return ToolResult(success=False, error=f"Unknown tool: {name}")

    except Exception as e:
        logger.error("tool_execution_failed", tool=name, error=str(e))
        return ToolResult(success=False, error=str(e))


async def execute_operation(dataset_id: str, operation: AnalyticalOperation) -> ToolResult:
    tool_map = {
        AnalyticalOperationType.FILTER: "filter_data",
        AnalyticalOperationType.SORT: "sort_data",
        AnalyticalOperationType.GROUP_BY: "group_by",
        AnalyticalOperationType.CALCULATE: "calculate_column",
        AnalyticalOperationType.RANK: "rank_data",
        AnalyticalOperationType.PERCENTAGE: "percentage_of_total",
        AnalyticalOperationType.GROWTH: "growth_rate",
        AnalyticalOperationType.STATISTICAL_SUMMARY: "statistical_summary",
        AnalyticalOperationType.CORRELATION: "correlation_matrix",
        AnalyticalOperationType.TREND: "trend_analysis",
        AnalyticalOperationType.OUTLIER: "detect_outliers",
        AnalyticalOperationType.MISSING_ANALYSIS: "missing_analysis",
    }

    tool_name = tool_map.get(operation.operation)
    if not tool_name:
        return ToolResult(success=False, error=f"Operation {operation.operation} not supported")

    tool_call = ToolCall(name=tool_name, arguments=operation.parameters)
    return await execute_tool(dataset_id, tool_call)