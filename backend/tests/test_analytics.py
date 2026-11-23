import pandas as pd

from app.services.analytics.service import AnalyticsService


class TestAnalyticsService:
    def setup_method(self):
        self.service = AnalyticsService()
        self.df = pd.DataFrame({
            "name": ["A", "B", "C", "D", "E"],
            "value": [10, 20, 30, 40, 50],
            "category": ["X", "Y", "X", "Y", "X"],
            "date": pd.date_range("2024-01-01", periods=5, freq="D"),
        })

    def test_filter_data_eq(self):
        result = self.service.filter_data(self.df, [{"column": "value", "operator": "eq", "value": 20}])
        assert len(result) == 1
        assert result.iloc[0]["value"] == 20

    def test_filter_data_gt(self):
        result = self.service.filter_data(self.df, [{"column": "value", "operator": "gt", "value": 25}])
        assert len(result) == 3
        assert all(result["value"] > 25)

    def test_filter_data_in(self):
        result = self.service.filter_data(self.df, [{"column": "category", "operator": "in", "value": ["X"]}])
        assert len(result) == 3
        assert all(result["category"] == "X")

    def test_filter_data_is_null(self):
        df_with_null = self.df.copy()
        df_with_null.loc[0, "value"] = None
        result = self.service.filter_data(df_with_null, [{"column": "value", "operator": "is_null", "value": None}])
        assert len(result) == 1

    def test_sort_data(self):
        result = self.service.sort_data(self.df, ["value"], ascending=[False])
        assert result.iloc[0]["value"] == 50
        assert result.iloc[-1]["value"] == 10

    def test_group_by(self):
        result = self.service.group_by(self.df, ["category"], {"value": "sum"})
        assert len(result) == 2
        x_sum = result[result["category"] == "X"]["value"].values[0]
        assert x_sum == 90  # 10 + 30 + 50

    def test_calculate_column(self):
        result = self.service.calculate_column(self.df, "double_value", "value * 2")
        assert "double_value" in result.columns
        assert result.iloc[0]["double_value"] == 20

    def test_rank_data(self):
        result = self.service.rank_data(self.df, "value", ascending=False)
        assert "value_rank" in result.columns
        # 50 is the highest value, should have rank 1
        max_value_row = result[result["value"] == 50]
        assert max_value_row["value_rank"].values[0] == 1

    def test_percentage_of_total(self):
        result = self.service.percentage_of_total(self.df, "value")
        assert "value_pct" in result.columns
        total = result["value_pct"].sum()
        assert abs(total - 100) < 0.01

    def test_percentage_of_total_grouped(self):
        result = self.service.percentage_of_total(self.df, "value", group_by=["category"])
        assert "value_pct" in result.columns

    def test_statistical_summary(self):
        summary = self.service.statistical_summary(self.df, ["value"])
        assert "value" in summary
        assert summary["value"]["count"] == 5
        assert summary["value"]["mean"] == 30
        assert summary["value"]["min"] == 10
        assert summary["value"]["max"] == 50

    def test_correlation_matrix(self):
        corr = self.service.correlation_matrix(self.df, ["value"])
        assert "value" in corr["columns"]
        assert corr["matrix"]["value"]["value"] == 1.0

    def test_detect_outliers_iqr(self):
        df_outliers = pd.DataFrame({"value": [1, 2, 3, 4, 5, 100]})
        outliers = self.service.detect_outliers(df_outliers, "value", method="iqr")
        assert outliers["count"] >= 1

    def test_detect_outliers_zscore(self):
        df_outliers = pd.DataFrame({"value": [1, 2, 3, 4, 5, 100]})
        outliers = self.service.detect_outliers(df_outliers, "value", method="zscore", threshold=2)
        assert outliers["count"] >= 1

    def test_trend_analysis(self):
        trend = self.service.trend_analysis(self.df, "date", "value")
        assert "trend" in trend
        assert "slope" in trend
        assert "r_squared" in trend
        assert trend["trend"] == "increasing"

    def test_missing_analysis(self):
        df_missing = self.df.copy()
        df_missing.loc[0, "value"] = None
        df_missing.loc[1, "category"] = None
        missing = self.service.missing_analysis(df_missing)
        assert missing["total_missing"] == 2
        assert "value" in missing["by_column"]
        assert "category" in missing["by_column"]