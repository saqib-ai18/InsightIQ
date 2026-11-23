import pandas as pd

from app.services.ingestion.service import IngestionService


class TestIngestionService:
    def setup_method(self):
        self.service = IngestionService()

    def test_validate_file_valid_csv(self):
        valid, error = self.service.validate_file("test.csv", 1024)
        assert valid is True
        assert error == ""

    def test_validate_file_invalid_extension(self):
        valid, error = self.service.validate_file("test.exe", 1024)
        assert valid is False
        assert "not allowed" in error

    def test_validate_file_too_large(self):
        valid, error = self.service.validate_file("test.csv", 200 * 1024 * 1024)
        assert valid is False
        assert "exceeds limit" in error

    def test_detect_file_type(self):
        assert self.service.detect_file_type("test.csv").value == "csv"
        assert self.service.detect_file_type("test.xlsx").value == "xlsx"
        assert self.service.detect_file_type("test.json").value == "json"
        assert self.service.detect_file_type("test.parquet").value == "parquet"

    def test_infer_column_type_integer(self):
        series = pd.Series([1, 2, 3, 4, 5])
        assert self.service.infer_column_type(series).value == "integer"

    def test_infer_column_type_float(self):
        series = pd.Series([1.1, 2.2, 3.3])
        assert self.service.infer_column_type(series).value == "float"

    def test_infer_column_type_string(self):
        series = pd.Series(["a", "b", "c"])
        assert self.service.infer_column_type(series).value == "string"

    def test_infer_column_type_category(self):
        series = pd.Series(["a", "b", "a", "b", "a"] * 10)
        assert self.service.infer_column_type(series).value == "category"

    def test_read_csv(self):
        csv_content = b"name,value\nA,1\nB,2\nC,3"
        file_path = self.service.upload_dir / "test.csv"
        file_path.write_bytes(csv_content)

        df = self.service.read_file(file_path, self.service.detect_file_type("test.csv"))
        assert len(df) == 3
        assert list(df.columns) == ["name", "value"]