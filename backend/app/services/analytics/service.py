import pandas as pd
import numpy as np
from scipy import stats
from typing import Any, Dict, List, Optional
import structlog
import duckdb
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


logger = structlog.get_logger()


class AnalyticsService:
    def __init__(self):
        self.conn = duckdb.connect()
        self.conn.execute("SET enable_progress_bar=false")

    def _register_dataframe(self, df: pd.DataFrame, name: str = "dataset") -> None:
        self.conn.register(name, df)

    def _execute_sql(self, query: str) -> pd.DataFrame:
        return self.conn.execute(query).fetchdf()

    def filter_data(
        self,
        df: pd.DataFrame,
        filters: List[Dict[str, Any]],
    ) -> pd.DataFrame:
        result = df.copy()
        for f in filters:
            column = f.get("column")
            operator = f.get("operator")
            value = f.get("value")

            if column not in result.columns:
                continue

            if operator == "eq":
                result = result[result[column] == value]
            elif operator == "neq":
                result = result[result[column] != value]
            elif operator == "gt":
                result = result[result[column] > value]
            elif operator == "gte":
                result = result[result[column] >= value]
            elif operator == "lt":
                result = result[result[column] < value]
            elif operator == "lte":
                result = result[result[column] <= value]
            elif operator == "in":
                result = result[result[column].isin(value)]
            elif operator == "not_in":
                result = result[~result[column].isin(value)]
            elif operator == "contains":
                result = result[result[column].astype(str).str.contains(str(value), na=False)]
            elif operator == "not_contains":
                result = result[~result[column].astype(str).str.contains(str(value), na=False)]
            elif operator == "starts_with":
                result = result[result[column].astype(str).str.startswith(str(value), na=False)]
            elif operator == "ends_with":
                result = result[result[column].astype(str).str.endswith(str(value), na=False)]
            elif operator == "is_null":
                result = result[result[column].isna()]
            elif operator == "is_not_null":
                result = result[result[column].notna()]
            elif operator == "between":
                if isinstance(value, list) and len(value) == 2:
                    result = result[(result[column] >= value[0]) & (result[column] <= value[1])]

        return result

    def sort_data(
        self,
        df: pd.DataFrame,
        columns: List[str],
        ascending: Optional[List[bool]] = None,
    ) -> pd.DataFrame:
        if ascending is None:
            ascending = [True] * len(columns)
        return df.sort_values(by=columns, ascending=ascending)

    def group_by(
        self,
        df: pd.DataFrame,
        group_columns: List[str],
        aggregations: Dict[str, str],
    ) -> pd.DataFrame:
        agg_funcs = {}
        for col, func in aggregations.items():
            if func == "count":
                agg_funcs[col] = "count"
            elif func == "count_distinct":
                agg_funcs[col] = "nunique"
            elif func == "sum":
                agg_funcs[col] = "sum"
            elif func == "mean":
                agg_funcs[col] = "mean"
            elif func == "median":
                agg_funcs[col] = "median"
            elif func == "min":
                agg_funcs[col] = "min"
            elif func == "max":
                agg_funcs[col] = "max"
            elif func == "std":
                agg_funcs[col] = "std"
            elif func == "var":
                agg_funcs[col] = "var"
            elif func == "first":
                agg_funcs[col] = "first"
            elif func == "last":
                agg_funcs[col] = "last"

        result = df.groupby(group_columns, as_index=False).agg(agg_funcs)
        result.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col for col in result.columns]
        return result

    def calculate_column(
        self,
        df: pd.DataFrame,
        new_column: str,
        expression: str,
    ) -> pd.DataFrame:
        result = df.copy()
        try:
            result[new_column] = result.eval(expression)
        except Exception as e:
            logger.error("calculate_column_failed", expression=expression, error=str(e))
            raise ValueError(f"Invalid expression: {expression}")
        return result

    def rank_data(
        self,
        df: pd.DataFrame,
        column: str,
        ascending: bool = False,
        method: str = "min",
    ) -> pd.DataFrame:
        result = df.copy()
        result[f"{column}_rank"] = result[column].rank(ascending=ascending, method=method)
        return result

    def percentage_of_total(
        self,
        df: pd.DataFrame,
        column: str,
        group_by: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        result = df.copy()
        if group_by:
            total = result.groupby(group_by)[column].transform("sum")
            result[f"{column}_pct"] = (result[column] / total * 100).round(2)
        else:
            total = result[column].sum()
            result[f"{column}_pct"] = (result[column] / total * 100).round(2)
        return result

    def growth_rate(
        self,
        df: pd.DataFrame,
        value_column: str,
        date_column: str,
        period: str = "M",
    ) -> pd.DataFrame:
        result = df.copy()
        result[date_column] = pd.to_datetime(result[date_column])
        result = result.sort_values(date_column)

        if period == "M":
            result["period"] = result[date_column].dt.to_period("M")
        elif period == "W":
            result["period"] = result[date_column].dt.to_period("W")
        elif period == "Q":
            result["period"] = result[date_column].dt.to_period("Q")
        elif period == "Y":
            result["period"] = result[date_column].dt.to_period("Y")

        period_sums = result.groupby("period")[value_column].sum().reset_index()
        period_sums = period_sums.sort_values("period")
        period_sums[f"{value_column}_prev"] = period_sums[value_column].shift(1)
        period_sums[f"{value_column}_growth"] = (
            (period_sums[value_column] - period_sums[f"{value_column}_prev"])
            / period_sums[f"{value_column}_prev"] * 100
        ).round(2)

        return period_sums

    def statistical_summary(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        summary = {}
        for col in columns:
            if col not in df.columns:
                continue
            series = df[col].dropna()
            if len(series) == 0:
                continue

            summary[col] = {
                "count": int(len(series)),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()) if len(series) > 1 else 0,
                "var": float(series.var()) if len(series) > 1 else 0,
                "min": float(series.min()),
                "max": float(series.max()),
                "q25": float(series.quantile(0.25)),
                "q50": float(series.quantile(0.50)),
                "q75": float(series.quantile(0.75)),
                "skewness": float(stats.skew(series)) if len(series) > 2 else 0,
                "kurtosis": float(stats.kurtosis(series)) if len(series) > 3 else 0,
                "missing": int(df[col].isna().sum()),
            }
        return summary

    def correlation_matrix(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "pearson",
    ) -> Dict[str, Any]:
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        numeric_df = df[columns].select_dtypes(include=[np.number])
        corr_matrix = numeric_df.corr(method=method)

        return {
            "columns": columns,
            "method": method,
            "matrix": corr_matrix.round(4).to_dict(),
        }

    def detect_outliers(
        self,
        df: pd.DataFrame,
        column: str,
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> Dict[str, Any]:
        series = df[column].dropna()
        if len(series) == 0:
            return {"outliers": [], "count": 0, "method": method}

        outliers = pd.Series(False, index=series.index)

        if method == "iqr":
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            outliers = (series < lower) | (series > upper)

        elif method == "zscore":
            z_scores = np.abs((series - series.mean()) / series.std())
            outliers = z_scores > threshold

        elif method == "modified_zscore":
            median = series.median()
            mad = np.median(np.abs(series - median))
            modified_z = 0.6745 * (series - median) / mad
            outliers = np.abs(modified_z) > threshold

        outlier_indices = series.index[outliers].tolist()
        outlier_values = series[outliers].tolist()

        return {
            "outliers": list(zip(outlier_indices, outlier_values)),
            "count": int(outliers.sum()),
            "method": method,
            "threshold": threshold,
        }

    def trend_analysis(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
    ) -> Dict[str, Any]:
        result = df.copy()
        result[date_column] = pd.to_datetime(result[date_column])
        result = result.sort_values(date_column)

        daily = result.groupby(date_column)[value_column].sum().reset_index()
        daily["day_num"] = np.arange(len(daily))

        if len(daily) < 2:
            return {"trend": "insufficient_data", "slope": 0, "r_squared": 0}

        x = daily["day_num"].values
        y = daily[value_column].values

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "flat"

        return {
            "trend": trend_direction,
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": float(r_value ** 2),
            "p_value": float(p_value),
            "std_err": float(std_err),
            "data_points": len(daily),
        }

    def missing_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        total_cells = df.size
        total_missing = df.isna().sum().sum()

        by_column = {}
        for col in df.columns:
            missing = int(df[col].isna().sum())
            if missing > 0:
                by_column[col] = {
                    "missing": missing,
                    "percentage": round(missing / len(df) * 100, 2),
                }

        return {
            "total_missing": int(total_missing),
            "total_cells": int(total_cells),
            "missing_percentage": round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0,
            "by_column": by_column,
            "rows_with_missing": int(df.isna().any(axis=1).sum()),
            "complete_rows": int(df.dropna().shape[0]),
        }

    def execute_sql(self, df: pd.DataFrame, query: str) -> pd.DataFrame:
        self._register_dataframe(df)
        try:
            result = self._execute_sql(query)
            return result
        except Exception as e:
            logger.error("sql_execution_failed", query=query, error=str(e))
            raise ValueError(f"SQL execution failed: {str(e)}")

    def forecast(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        horizon: int = 6,
        freq: str = "M",
    ) -> Dict[str, Any]:
        result = df.copy()
        result[date_column] = pd.to_datetime(result[date_column])
        result = result.sort_values(date_column)

        if freq == "D":
            result["period"] = result[date_column].dt.to_period("D")
        elif freq == "W":
            result["period"] = result[date_column].dt.to_period("W")
        elif freq == "M":
            result["period"] = result[date_column].dt.to_period("M")
        elif freq == "Q":
            result["period"] = result[date_column].dt.to_period("Q")
        elif freq == "Y":
            result["period"] = result[date_column].dt.to_period("Y")

        period_sums = result.groupby("period")[value_column].sum().reset_index()
        period_sums = period_sums.sort_values("period")
        
        if len(period_sums) < 3:
            return {"forecast": [], "confidence_intervals": [], "model": "insufficient_data"}

        period_sums["period_num"] = np.arange(len(period_sums))
        
        X = period_sums[["period_num"]].values
        y = period_sums[value_column].values

        model = LinearRegression()
        model.fit(X, y)

        y_pred = model.predict(X)
        residuals = y - y_pred
        mse = np.mean(residuals ** 2)
        std_err = np.sqrt(mse)

        future_periods = np.arange(len(period_sums), len(period_sums) + horizon).reshape(-1, 1)
        forecast_values = model.predict(future_periods)

        confidence_95 = 1.96 * std_err
        lower_bound = forecast_values - confidence_95
        upper_bound = forecast_values + confidence_95

        last_period = period_sums["period"].iloc[-1]
        future_periods_list = []
        for i in range(horizon):
            if freq == "D":
                next_period = last_period + pd.DateOffset(days=i+1)
            elif freq == "W":
                next_period = last_period + pd.DateOffset(weeks=i+1)
            elif freq == "M":
                next_period = last_period + pd.DateOffset(months=i+1)
            elif freq == "Q":
                next_period = last_period + pd.DateOffset(months=3*(i+1))
            elif freq == "Y":
                next_period = last_period + pd.DateOffset(years=i+1)
            future_periods_list.append(str(next_period))

        r_squared = model.score(X, y)

        return {
            "forecast": [
                {
                    "period": future_periods_list[i],
                    "value": round(float(forecast_values[i]), 2),
                    "lower": round(float(lower_bound[i]), 2),
                    "upper": round(float(upper_bound[i]), 2),
                }
                for i in range(horizon)
            ],
            "confidence_intervals": {
                "level": 0.95,
                "lower": lower_bound.tolist(),
                "upper": upper_bound.tolist(),
            },
            "model": "linear_regression",
            "r_squared": round(r_squared, 4),
            "trend": "increasing" if model.coef_[0] > 0 else "decreasing",
            "historical_data": [
                {"period": str(p), "value": float(v)}
                for p, v in zip(period_sums["period"], period_sums[value_column])
            ],
        }

    def anomaly_detection(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        contamination: float = 0.05,
        method: str = "isolation_forest",
    ) -> Dict[str, Any]:
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if not columns:
            return {"anomalies": [], "count": 0, "method": method}

        data = df[columns].dropna()
        if len(data) == 0:
            return {"anomalies": [], "count": 0, "method": method}

        if method == "isolation_forest":
            clf = IsolationForest(contamination=contamination, random_state=42)
            preds = clf.fit_predict(data)
            scores = clf.decision_function(data)
            
            anomaly_indices = np.where(preds == -1)[0]
            anomaly_scores = scores[anomaly_indices]
            
            anomalies = []
            for idx, score in zip(anomaly_indices, anomaly_scores):
                anomalies.append({
                    "row_index": int(data.index[idx]),
                    "score": round(float(-score), 4),
                    "values": {col: float(data.iloc[idx][col]) for col in columns},
                })
            
            return {
                "anomalies": anomalies,
                "count": len(anomalies),
                "method": "isolation_forest",
                "contamination": contamination,
            }
        
        elif method == "statistical":
            anomalies = []
            for col in columns:
                series = data[col]
                mean = series.mean()
                std = series.std()
                threshold = 3 * std
                outliers = series[(series - mean).abs() > threshold]
                
                for idx in outliers.index:
                    anomalies.append({
                        "row_index": int(idx),
                        "column": col,
                        "value": float(outliers[idx]),
                        "z_score": round(float((outliers[idx] - mean) / std), 4),
                    })
            
            return {
                "anomalies": anomalies,
                "count": len(anomalies),
                "method": "statistical",
                "threshold": "3 std",
            }
        
        else:
            return {"anomalies": [], "count": 0, "method": method, "error": "Unknown method"}

    def customer_segmentation(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        n_clusters: int = 4,
    ) -> Dict[str, Any]:
        data = df[feature_columns].dropna()
        if len(data) == 0:
            return {"segments": [], "count": 0, "error": "No valid data"}

        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(scaled_data)

        segments = []
        for i in range(n_clusters):
            segment_data = data[labels == i]
            segments.append({
                "segment_id": i,
                "size": int((labels == i).sum()),
                "percentage": round((labels == i).sum() / len(labels) * 100, 1),
                "centroid": {col: float(kmeans.cluster_centers_[i][j]) for j, col in enumerate(feature_columns)},
                "mean_values": {col: float(segment_data[col].mean()) for col in feature_columns},
            })

        result_df = df.loc[data.index].copy()
        result_df["segment"] = labels

        return {
            "segments": segments,
            "count": len(segments),
            "method": "kmeans",
            "n_clusters": n_clusters,
            "features": feature_columns,
            "labels": labels.tolist(),
        }


analytics_service = AnalyticsService()