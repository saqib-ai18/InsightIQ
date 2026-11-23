import pandas as pd
import structlog
from typing import Any, Dict, List, Optional

from app.services.ingestion.service import ingestion_service

logger = structlog.get_logger()


class VisualizationService:
    def __init__(self):
        pass

    def suggest_charts(self, dataset_id: str) -> List[Dict[str, Any]]:
        try:
            df = ingestion_service.load_dataframe(dataset_id)
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.error("load_dataset_failed", dataset_id=dataset_id, error=str(e))
            return []

        suggestions = []
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        date_cols = df.select_dtypes(include=["datetime", "date"]).columns.tolist()

        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            suggestions.append({
                "chart_type": "bar",
                "title": f"{numeric_cols[0]} by {categorical_cols[0]}",
                "x_column": categorical_cols[0],
                "y_columns": [numeric_cols[0]],
                "reason": "Compare numeric values across categories",
            })

        if len(categorical_cols) >= 1:
            suggestions.append({
                "chart_type": "pie",
                "title": f"Distribution of {categorical_cols[0]}",
                "x_column": categorical_cols[0],
                "y_columns": [],
                "reason": "Show category proportions",
            })

        if len(date_cols) >= 1 and len(numeric_cols) >= 1:
            suggestions.append({
                "chart_type": "line",
                "title": f"{numeric_cols[0]} over time",
                "x_column": date_cols[0],
                "y_columns": [numeric_cols[0]],
                "reason": "Show trends over time",
            })

        if len(numeric_cols) >= 2:
            suggestions.append({
                "chart_type": "scatter",
                "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                "x_column": numeric_cols[0],
                "y_columns": [numeric_cols[1]],
                "reason": "Show relationship between two numeric variables",
            })

        if len(numeric_cols) >= 1:
            suggestions.append({
                "chart_type": "histogram",
                "title": f"Distribution of {numeric_cols[0]}",
                "x_column": numeric_cols[0],
                "y_columns": [],
                "reason": "Show distribution of a numeric variable",
            })

        if len(numeric_cols) >= 2:
            suggestions.append({
                "chart_type": "box",
                "title": f"Box plot of {numeric_cols[0]} by {categorical_cols[0] if categorical_cols else numeric_cols[1]}",
                "x_column": categorical_cols[0] if categorical_cols else numeric_cols[1],
                "y_columns": [numeric_cols[0]],
                "reason": "Show distribution and outliers",
            })

        if len(numeric_cols) >= 3:
            suggestions.append({
                "chart_type": "heatmap",
                "title": "Correlation heatmap",
                "x_column": "",
                "y_columns": numeric_cols[:5],
                "reason": "Show correlations between numeric variables",
            })

        return suggestions[:8]

    def generate_chart_data(
        self,
        dataset_id: str,
        chart_type: str,
        x_column: str,
        y_columns: List[str],
        group_by: Optional[str] = None,
        filters: Optional[List[Dict]] = None,
        aggregation: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        try:
            df = ingestion_service.load_dataframe(dataset_id)
        except FileNotFoundError:
            raise ValueError("Dataset not found")
        except Exception as e:
            logger.error("load_dataset_failed", dataset_id=dataset_id, error=str(e))
            raise

        if filters:
            for f in filters:
                col = f.get("column")
                op = f.get("operator")
                val = f.get("value")
                if col and op and val is not None:
                    if op == "eq":
                        df = df[df[col] == val]
                    elif op == "neq":
                        df = df[df[col] != val]
                    elif op == "gt":
                        df = df[df[col] > val]
                    elif op == "gte":
                        df = df[df[col] >= val]
                    elif op == "lt":
                        df = df[df[col] < val]
                    elif op == "lte":
                        df = df[df[col] <= val]
                    elif op == "in":
                        df = df[df[col].isin(val)]
                    elif op == "not_in":
                        df = df[~df[col].isin(val)]
                    elif op == "contains":
                        df = df[df[col].astype(str).str.contains(str(val), na=False)]
                    elif op == "is_null":
                        df = df[df[col].isna()]
                    elif op == "is_not_null":
                        df = df[df[col].notna()]

        if group_by:
            if chart_type in ["pie"]:
                df = df.groupby(group_by).size().reset_index(name="count")
            elif chart_type in ["bar", "line", "area", "scatter", "box"]:
                agg_func = aggregation or "mean"
                agg_map = {
                    "sum": "sum",
                    "mean": "mean",
                    "median": "median",
                    "min": "min",
                    "max": "max",
                    "count": "count",
                }
                agg = agg_map.get(agg_func, "mean")
                if y_columns:
                    df = df.groupby(group_by)[y_columns].agg(agg).reset_index()
                else:
                    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                    if numeric_cols:
                        df = df.groupby(group_by)[numeric_cols].agg(agg).reset_index()
            else:
                df = df.groupby(group_by).size().reset_index(name="count")

        if limit:
            df = df.head(limit)

        chart_data = self._format_chart_data(df, chart_type, x_column, y_columns, group_by)

        return chart_data

    def _format_chart_data(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x_column: str,
        y_columns: List[str],
        group_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        if df.empty:
            return {"categories": [], "series": []}

        if chart_type in ["pie", "donut"]:
            if group_by:
                values = df.iloc[:, 1].tolist() if len(df.columns) > 1 else df.iloc[:, 0].tolist()
                labels = df.iloc[:, 0].tolist()
            else:
                values = df.iloc[:, 0].tolist() if len(df) > 0 else []
                labels = df.index.astype(str).tolist()

            return {
                "type": chart_type,
                "categories": labels,
                "series": [{
                    "name": "Distribution",
                    "data": [{"value": val, "name": label} for val, label in zip(values, labels)],
                }],
            }

        elif chart_type in ["bar", "horizontal_bar"]:
            if group_by:
                categories = df[group_by].astype(str).tolist()
            elif x_column and x_column in df.columns:
                categories = df[x_column].astype(str).tolist()
            else:
                categories = df.index.astype(str).tolist()

            series = []
            for y_col in y_columns:
                if y_col in df.columns:
                    series.append({
                        "name": y_col,
                        "type": "bar" if chart_type == "bar" else "bar",
                        "data": df[y_col].tolist(),
                    })

            return {
                "type": chart_type,
                "categories": categories,
                "series": series,
            }

        elif chart_type in ["line", "area"]:
            if x_column and x_column in df.columns:
                categories = df[x_column].astype(str).tolist()
            elif group_by and group_by in df.columns:
                categories = df[group_by].astype(str).tolist()
            else:
                categories = df.index.astype(str).tolist()

            series = []
            for y_col in y_columns:
                if y_col in df.columns:
                    series.append({
                        "name": y_col,
                        "type": "line",
                        "data": df[y_col].tolist(),
                        "areaStyle": {} if chart_type == "area" else None,
                    })

            return {
                "type": chart_type,
                "categories": categories,
                "series": series,
            }

        elif chart_type == "scatter":
            if len(y_columns) >= 1 and x_column and x_column in df.columns:
                data = []
                for _, row in df.iterrows():
                    point = {"value": [row[x_column], row[y_columns[0]]]}
                    if len(y_columns) > 1 and y_columns[1] in df.columns:
                        point["value"].append(row[y_columns[1]])
                    data.append(point)

                return {
                    "type": "scatter",
                    "series": [{
                        "name": "Scatter",
                        "type": "scatter",
                        "data": data,
                    }],
                }
            return {"categories": [], "series": []}

        elif chart_type == "histogram":
            if x_column and x_column in df.columns:
                data = df[x_column].dropna().tolist()
                return {
                    "type": "histogram",
                    "series": [{
                        "name": x_column,
                        "type": "histogram",
                        "data": data,
                    }],
                }
            return {"categories": [], "series": []}

        elif chart_type == "box":
            if group_by and group_by in df.columns and y_columns:
                categories = df[group_by].unique().tolist()
                series = []
                for cat in categories:
                    cat_data = df[df[group_by] == cat][y_columns[0]].dropna().tolist()
                    if cat_data:
                        q1 = pd.Series(cat_data).quantile(0.25)
                        q3 = pd.Series(cat_data).quantile(0.75)
                        median = pd.Series(cat_data).median()
                        min_val = min(cat_data)
                        max_val = max(cat_data)
                        series.append({
                            "name": str(cat),
                            "data": [min_val, q1, median, q3, max_val],
                        })
                return {
                    "type": "box",
                    "categories": [str(c) for c in categories],
                    "series": series,
                }
            return {"categories": [], "series": []}

        elif chart_type == "heatmap":
            if len(y_columns) >= 2:
                corr_matrix = df[y_columns].corr()
                heatmap_data: list = []
                for i, row_name in enumerate(corr_matrix.index):
                    for j, col_name in enumerate(corr_matrix.columns):
                        heatmap_data.append([j, i, round(corr_matrix.iloc[i, j], 2)])

                return {
                    "type": "heatmap",
                    "categories": y_columns,
                    "series": [{
                        "name": "Correlation",
                        "data": heatmap_data,
                    }],
                }  # type: ignore[return-value]

        return {"categories": [], "series": []}


visualization_service = VisualizationService()