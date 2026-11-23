import re
import structlog
from typing import Any, Dict, List, Optional, Set
from enum import Enum

logger = structlog.get_logger()


class SQLDialect(str, Enum):
    DUCKDB = "duckdb"


class SQLSecurityError(Exception):
    pass


class SQLGenerator:
    def __init__(self):
        self.allowed_tables: Set[str] = {"dataset"}
        self.blocked_keywords: Set[str] = {
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
            "TRUNCATE", "REPLACE", "MERGE", "COPY", "EXPORT",
            "ATTACH", "DETACH", "PRAGMA", "SET", "RESET",
            "LOAD", "INSTALL", "UNINSTALL",
        }
        self.max_query_length = 10000
        self.query_timeout_ms = 30000

    def _get_numeric_columns(self, columns: List[str], df=None) -> List[str]:
        if df is not None:
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            return [c for c in columns if c in numeric_cols]
        numeric_indicators = ["id", "count", "value", "price", "amount", "total", "sum", "avg", "mean", "median", "score", "rate", "ratio", "percent", "quantity", "qty", "num", "int", "float", "double"]
        return [c for c in columns if any(ind in c.lower() for ind in numeric_indicators)]

    def _get_date_columns(self, columns: List[str], df=None) -> List[str]:
        if df is not None:
            try:
                date_cols = df.select_dtypes(include=["datetime", "date"]).columns.tolist()
                return [c for c in columns if c in date_cols]
            except Exception:
                pass
        date_indicators = ["date", "time", "created", "updated", "timestamp", "dt", "year", "month", "day"]
        return [c for c in columns if any(ind in c.lower() for ind in date_indicators)]

    def validate_sql(self, sql: str, dataset_columns: List[str]) -> Dict[str, Any]:
        sql_upper = sql.upper().strip()

        if not sql_upper:
            return {"valid": False, "error": "Empty query"}

        if len(sql) > self.max_query_length:
            return {"valid": False, "error": f"Query exceeds maximum length of {self.max_query_length} characters"}

        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return {"valid": False, "error": "Only SELECT queries and CTEs are allowed"}

        for keyword in self.blocked_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, sql_upper):
                return {"valid": False, "error": f"Blocked keyword detected: {keyword}"}

        table_refs = self._extract_table_references(sql_upper)
        for table in table_refs:
            if table not in self.allowed_tables:
                return {"valid": False, "error": f"Unauthorized table reference: {table}"}

        if ";" in sql.rstrip()[:-1]:
            return {"valid": False, "error": "Multiple statements not allowed"}

        return {"valid": True, "sanitized_sql": sql}

    def _extract_table_references(self, sql: str) -> Set[str]:
        tables = set()
        from_pattern = r'\bFROM\s+(\w+)'
        join_pattern = r'\bJOIN\s+(\w+)'

        for match in re.finditer(from_pattern, sql):
            tables.add(match.group(1).lower())
        for match in re.finditer(join_pattern, sql):
            tables.add(match.group(1).lower())

        return tables

    def generate_sql_from_nl(
        self,
        question: str,
        dataset_columns: List[str],
        df=None,
        dataset_sample: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        question_lower = question.lower()

        if any(kw in question_lower for kw in ["top", "highest", "maximum", "largest", "best"]):
            return self._generate_top_n_sql(question, dataset_columns, df)
        elif any(kw in question_lower for kw in ["bottom", "lowest", "minimum", "smallest", "worst"]):
            return self._generate_bottom_n_sql(question, dataset_columns, df)
        elif any(kw in question_lower for kw in ["average", "mean", "avg"]):
            return self._generate_avg_sql(question, dataset_columns, df)
        elif any(kw in question_lower for kw in ["sum", "total", "sum of"]):
            return self._generate_sum_sql(question, dataset_columns, df)
        elif any(kw in question_lower for kw in ["count", "how many", "number of"]):
            return self._generate_count_sql(question, dataset_columns, df)
        elif any(kw in question_lower for kw in ["group by", "grouped by", "per ", "by "]):
            return self._generate_group_by_sql(question, dataset_columns, df)
        elif any(kw in question_lower for kw in ["trend", "over time", "monthly", "yearly", "daily"]):
            return self._generate_trend_sql(question, dataset_columns, df)
        elif any(kw in question_lower for kw in ["correlation", "correlate", "relationship between"]):
            return self._generate_correlation_sql(question, dataset_columns, df)
        else:
            return self._generate_generic_sql(question, dataset_columns)

    def _generate_top_n_sql(self, question: str, columns: List[str], df=None) -> Dict[str, Any]:
        numeric_cols = self._get_numeric_columns(columns, df)
        n = 10
        numbers = re.findall(r'\b(\d+)\b', question)
        if numbers:
            n = int(numbers[0])

        metric_col = numeric_cols[0] if numeric_cols else columns[0]
        dimension_col = columns[0] if columns else "name"

        sql = f"SELECT {dimension_col}, {metric_col} FROM dataset ORDER BY {metric_col} DESC LIMIT {n}"
        return {"sql": sql, "explanation": f"Top {n} {dimension_col} by {metric_col}"}

    def _generate_bottom_n_sql(self, question: str, columns: List[str], df=None) -> Dict[str, Any]:
        numeric_cols = self._get_numeric_columns(columns, df)
        n = 10
        numbers = re.findall(r'\b(\d+)\b', question)
        if numbers:
            n = int(numbers[0])

        metric_col = numeric_cols[0] if numeric_cols else columns[0]
        dimension_col = columns[0] if columns else "name"

        sql = f"SELECT {dimension_col}, {metric_col} FROM dataset ORDER BY {metric_col} ASC LIMIT {n}"
        return {"sql": sql, "explanation": f"Bottom {n} {dimension_col} by {metric_col}"}

    def _generate_avg_sql(self, question: str, columns: List[str], df=None) -> Dict[str, Any]:
        numeric_cols = self._get_numeric_columns(columns, df)
        metric_col = numeric_cols[0] if numeric_cols else columns[0]

        if "by" in question.lower() or "per" in question.lower():
            dimension_col = columns[0]
            sql = f"SELECT {dimension_col}, AVG({metric_col}) as avg_{metric_col} FROM dataset GROUP BY {dimension_col} ORDER BY avg_{metric_col} DESC"
        else:
            sql = f"SELECT AVG({metric_col}) as avg_{metric_col} FROM dataset"

        return {"sql": sql, "explanation": f"Average of {metric_col}"}

    def _generate_sum_sql(self, question: str, columns: List[str], df=None) -> Dict[str, Any]:
        numeric_cols = self._get_numeric_columns(columns, df)
        metric_col = numeric_cols[0] if numeric_cols else columns[0]

        if "by" in question.lower() or "per" in question.lower():
            dimension_col = columns[0]
            sql = f"SELECT {dimension_col}, SUM({metric_col}) as total_{metric_col} FROM dataset GROUP BY {dimension_col} ORDER BY total_{metric_col} DESC"
        else:
            sql = f"SELECT SUM({metric_col}) as total_{metric_col} FROM dataset"

        return {"sql": sql, "explanation": f"Sum of {metric_col}"}

    def _generate_count_sql(self, question: str, columns: List[str], df=None) -> Dict[str, Any]:
        if "distinct" in question.lower() or "unique" in question.lower():
            col = columns[0]
            sql = f"SELECT COUNT(DISTINCT {col}) as unique_count FROM dataset"
        elif "by" in question.lower() or "per" in question.lower():
            dimension_col = columns[0]
            sql = f"SELECT {dimension_col}, COUNT(*) as count FROM dataset GROUP BY {dimension_col} ORDER BY count DESC"
        else:
            sql = "SELECT COUNT(*) as total_count FROM dataset"

        return {"sql": sql, "explanation": "Count of records"}

    def _generate_group_by_sql(self, question: str, columns: List[str], df=None) -> Dict[str, Any]:
        dimension_col = columns[0]
        numeric_cols = self._get_numeric_columns(columns, df)
        metric_col = numeric_cols[0] if numeric_cols else columns[1] if len(columns) > 1 else columns[0]

        sql = f"SELECT {dimension_col}, COUNT(*) as count, AVG({metric_col}) as avg_{metric_col}, SUM({metric_col}) as sum_{metric_col} FROM dataset GROUP BY {dimension_col} ORDER BY count DESC"
        return {"sql": sql, "explanation": f"Grouped by {dimension_col} with aggregations on {metric_col}"}

    def _generate_trend_sql(self, question: str, columns: List[str], df=None) -> Dict[str, Any]:
        date_cols = self._get_date_columns(columns, df)
        numeric_cols = self._get_numeric_columns(columns, df)

        if date_cols and numeric_cols:
            date_col = date_cols[0]
            metric_col = numeric_cols[0]
            sql = f"SELECT DATE_TRUNC('month', {date_col}) as month, SUM({metric_col}) as total_{metric_col} FROM dataset GROUP BY month ORDER BY month"
            return {"sql": sql, "explanation": f"Monthly trend of {metric_col}"}
        else:
            return {"sql": "SELECT 1 as placeholder FROM dataset LIMIT 1", "explanation": "Insufficient date/numeric columns for trend analysis"}

    def _generate_correlation_sql(self, question: str, columns: List[str], df=None) -> Dict[str, Any]:
        numeric_cols = self._get_numeric_columns(columns, df)
        if len(numeric_cols) >= 2:
            col1, col2 = numeric_cols[0], numeric_cols[1]
            sql = f"SELECT CORR({col1}, {col2}) as correlation FROM dataset"
            return {"sql": sql, "explanation": f"Correlation between {col1} and {col2}"}
        else:
            return {"sql": "SELECT 1 as placeholder FROM dataset LIMIT 1", "explanation": "Insufficient numeric columns for correlation"}

    def _generate_generic_sql(self, question: str, columns: List[str]) -> Dict[str, Any]:
        dimension_col = columns[0] if columns else "name"
        metric_col = columns[1] if len(columns) > 1 else columns[0]

        sql = f"SELECT {dimension_col}, {metric_col} FROM dataset LIMIT 100"
        return {"sql": sql, "explanation": "Sample data preview"}


sql_generator = SQLGenerator()