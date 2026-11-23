import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Optional
import structlog

from app.schemas.profiling import (
    ColumnProfile, DatasetProfile, DataQualityIssue, DataQualityIssueType,
    NumericalStats, CategoricalStats, DateTimeStats
)
from app.services.ingestion.service import ingestion_service

logger = structlog.get_logger()


class ProfilingService:
    def __init__(self):
        self.settings = ingestion_service.settings

    def profile_dataset(self, dataset_id: str) -> DatasetProfile:
        df = ingestion_service.load_dataframe(dataset_id)
        metadata = self._get_metadata(dataset_id, df)

        columns = []
        all_issues = []

        for col_name in df.columns:
            col_profile = self._profile_column(df[col_name], col_name)
            columns.append(col_profile)
            all_issues.extend(col_profile.quality_issues)

        quality_score = self._calculate_quality_score(df, all_issues)
        recommendations = self._generate_recommendations(df, all_issues)

        return DatasetProfile(
            dataset_id=dataset_id,
            dataset_name=metadata.name,
            row_count=len(df),
            column_count=len(df.columns),
            memory_usage_mb=round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
            columns=columns,
            quality_score=quality_score,
            quality_issues=all_issues,
            recommendations=recommendations,
            profiled_at=pd.Timestamp.utcnow().isoformat(),
        )

    def _get_metadata(self, dataset_id: str, df: pd.DataFrame):
        datasets = ingestion_service.list_datasets()
        for ds in datasets:
            if ds.id == dataset_id:
                return ds
        from datetime import datetime
        from app.schemas.dataset import DatasetMetadata, FileType
        return DatasetMetadata(
            id=dataset_id,
            name="Unknown",
            original_filename="Unknown",
            file_type=FileType.CSV,
            file_size_bytes=0,
            row_count=len(df),
            column_count=len(df.columns),
            columns=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def _profile_column(self, series: pd.Series, name: str) -> ColumnProfile:

        col_type = ingestion_service.infer_column_type(series)
        issues = []
        sample_values = series.dropna().head(10).tolist()

        stats_obj: NumericalStats | CategoricalStats | DateTimeStats
        if pd.api.types.is_numeric_dtype(series):
            stats_obj = self._profile_numerical(series)
            issues.extend(self._check_numerical_issues(series, name, stats_obj))
        elif pd.api.types.is_datetime64_any_dtype(series):
            stats_obj = self._profile_datetime(series)
            issues.extend(self._check_datetime_issues(series, name))
        else:
            stats_obj = self._profile_categorical(series)
            issues.extend(self._check_categorical_issues(series, name, stats_obj))

        return ColumnProfile(
            name=name,
            type=col_type.value,
            stats=stats_obj,
            quality_issues=issues,
            sample_values=sample_values,
        )

    def _profile_numerical(self, series: pd.Series) -> NumericalStats:
        clean = series.dropna()
        if len(clean) == 0:
            return NumericalStats(count=0, missing=int(series.isnull().sum()))

        return NumericalStats(
            count=len(clean),
            mean=float(clean.mean()),
            median=float(clean.median()),
            mode=float(clean.mode().iloc[0]) if not clean.mode().empty else None,
            std=float(clean.std()) if len(clean) > 1 else None,
            variance=float(clean.var()) if len(clean) > 1 else None,
            min=float(clean.min()),
            max=float(clean.max()),
            range=float(clean.max() - clean.min()),
            q25=float(clean.quantile(0.25)),
            q50=float(clean.quantile(0.50)),
            q75=float(clean.quantile(0.75)),
            iqr=float(clean.quantile(0.75) - clean.quantile(0.25)),
            skewness=float(stats.skew(clean)) if len(clean) > 2 else None,
            kurtosis=float(stats.kurtosis(clean)) if len(clean) > 3 else None,
            missing=int(series.isnull().sum()),
            zeros=int((clean == 0).sum()),
            negative=int((clean < 0).sum()),
            positive=int((clean > 0).sum()),
        )

    def _profile_categorical(self, series: pd.Series) -> CategoricalStats:
        clean = series.dropna()
        if len(clean) == 0:
            return CategoricalStats(count=0, unique=0, missing=int(series.isnull().sum()))

        value_counts = clean.value_counts()
        top = value_counts.index[0] if len(value_counts) > 0 else None
        freq = int(value_counts.iloc[0]) if len(value_counts) > 0 else 0

        return CategoricalStats(
            count=len(clean),
            unique=clean.nunique(),
            top=str(top) if top is not None else None,
            freq=freq,
            distribution=value_counts.head(20).to_dict(),
            missing=int(series.isnull().sum()),
            cardinality_ratio=clean.nunique() / len(clean) if len(clean) > 0 else 0,
        )

    def _profile_datetime(self, series: pd.Series) -> DateTimeStats:
        clean = series.dropna()
        if len(clean) == 0:
            return DateTimeStats(count=0, missing=int(series.isnull().sum()))

        min_dt = clean.min()
        max_dt = clean.max()
        range_days = (max_dt - min_dt).days if pd.notna(min_dt) and pd.notna(max_dt) else None

        return DateTimeStats(
            count=len(clean),
            min=min_dt.isoformat() if pd.notna(min_dt) else None,
            max=max_dt.isoformat() if pd.notna(max_dt) else None,
            range_days=range_days,
            missing=int(series.isnull().sum()),
            frequency=self._infer_frequency(clean),
        )

    def _infer_frequency(self, series: pd.Series) -> Optional[str]:
        if len(series) < 3:
            return None
        try:
            diff = series.sort_values().diff().dropna()
            median_diff = diff.median()
            if median_diff <= pd.Timedelta(days=1):
                return "daily"
            elif median_diff <= pd.Timedelta(weeks=1):
                return "weekly"
            elif median_diff <= pd.Timedelta(days=31):
                return "monthly"
            elif median_diff <= pd.Timedelta(days=366):
                return "yearly"
        except Exception:
            pass
        return None

    def _check_numerical_issues(
        self, series: pd.Series, name: str, stats: NumericalStats
    ) -> List[DataQualityIssue]:
        issues = []
        missing = stats.missing
        total = len(series)

        if missing > 0:
            issues.append(DataQualityIssue(
                type=DataQualityIssueType.MISSING_VALUES,
                column=name,
                severity="high" if missing / total > 0.1 else "medium",
                message=f"Column has {missing} missing values ({missing/total*100:.1f}%)",
                count=missing,
                recommendation="Consider imputation or removal depending on analysis needs",
            ))

        if stats.std and stats.std > 0:
            z_scores = np.abs((series.dropna() - stats.mean) / stats.std)
            outliers = int((z_scores > 3).sum())
            if outliers > 0:
                issues.append(DataQualityIssue(
                    type=DataQualityIssueType.OUTLIER,
                    column=name,
                    severity="medium",
                    message=f"Column has {outliers} potential outliers (Z-score > 3)",
                    count=outliers,
                    recommendation="Review outliers for data entry errors or genuine anomalies",
                ))

        if stats.min == stats.max:
            issues.append(DataQualityIssue(
                type=DataQualityIssueType.CONSTANT_COLUMN,
                column=name,
                severity="low",
                message="Column has constant value",
                count=total,
                recommendation="Consider removing this column as it provides no information",
            ))

        return issues

    def _check_categorical_issues(
        self, series: pd.Series, name: str, stats: CategoricalStats
    ) -> List[DataQualityIssue]:
        issues = []
        missing = stats.missing
        total = len(series)

        if missing > 0:
            issues.append(DataQualityIssue(
                type=DataQualityIssueType.MISSING_VALUES,
                column=name,
                severity="high" if missing / total > 0.1 else "medium",
                message=f"Column has {missing} missing values ({missing/total*100:.1f}%)",
                count=missing,
                recommendation="Consider imputation with mode or 'Unknown' category",
            ))

        if stats.cardinality_ratio > 0.9 and stats.unique > 50:
            issues.append(DataQualityIssue(
                type=DataQualityIssueType.HIGH_CARDINALITY,
                column=name,
                severity="medium",
                message=f"Column has high cardinality ({stats.unique} unique values)",
                count=stats.unique,
                recommendation="Consider grouping rare categories or using target encoding",
            ))

        if stats.unique == 1:
            issues.append(DataQualityIssue(
                type=DataQualityIssueType.CONSTANT_COLUMN,
                column=name,
                severity="low",
                message="Column has only one unique value",
                count=total,
                recommendation="Consider removing this column",
            ))

        return issues

    def _check_datetime_issues(
        self, series: pd.Series, name: str
    ) -> List[DataQualityIssue]:
        issues = []
        missing = int(series.isnull().sum())
        total = len(series)

        if missing > 0:
            issues.append(DataQualityIssue(
                type=DataQualityIssueType.MISSING_VALUES,
                column=name,
                severity="high" if missing / total > 0.1 else "medium",
                message=f"Column has {missing} missing values ({missing/total*100:.1f}%)",
                count=missing,
                recommendation="Consider forward/backward fill for time series data",
            ))

        return issues

    def _calculate_quality_score(self, df: pd.DataFrame, issues: List[DataQualityIssue]) -> float:
        if len(df) == 0:
            return 0.0

        score = 100.0
        severity_weights = {"high": 10, "medium": 5, "low": 1}

        for issue in issues:
            weight = severity_weights.get(issue.severity, 5)
            impact = min(weight * (issue.count / len(df)) * 100, weight * 2)
            score -= impact

        return round(max(0, score), 1)

    def _generate_recommendations(self, df: pd.DataFrame, issues: List[DataQualityIssue]) -> List[str]:
        recommendations = []

        missing_cols = [i.column for i in issues if i.type == DataQualityIssueType.MISSING_VALUES and i.column]
        if missing_cols:
            unique_missing = list(set(missing_cols))
            recommendations.append(f"Handle missing values in {len(missing_cols)} columns: {', '.join(unique_missing[:5])}")

        outlier_cols = [i.column for i in issues if i.type == DataQualityIssueType.OUTLIER and i.column]
        if outlier_cols:
            recommendations.append(f"Review outliers in {len(outlier_cols)} numerical columns")

        high_card_cols = [i.column for i in issues if i.type == DataQualityIssueType.HIGH_CARDINALITY and i.column]
        if high_card_cols:
            unique_high_card = list(set(high_card_cols))
            recommendations.append(f"Consider encoding strategies for high cardinality columns: {', '.join(unique_high_card[:3])}")

        const_cols = [i.column for i in issues if i.type == DataQualityIssueType.CONSTANT_COLUMN and i.column]
        if const_cols:
            unique_const = list(set(const_cols))
            recommendations.append(f"Remove {len(const_cols)} constant columns: {', '.join(unique_const[:5])}")

        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            recommendations.append(f"Remove {dup_count} duplicate rows")

        if not recommendations:
            recommendations.append("Data quality looks good! No major issues detected.")

        return recommendations


profiling_service = ProfilingService()