import time
import os
from pathlib import Path
from typing import Optional
import structlog
from app.core.config import get_settings
from app.core.database import get_db_session
from app.models.database import DatasetModel

logger = structlog.get_logger()


class CleanupService:
    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.UPLOAD_DIR)
        self.max_file_age_seconds = 86400 * 7  # 7 days
        self.max_temp_file_age_seconds = 3600  # 1 hour

    def cleanup_old_uploads(self) -> int:
        """Remove uploaded files older than max_file_age_seconds."""
        if not self.upload_dir.exists():
            return 0

        cleaned = 0
        now = time.time()

        for file_path in self.upload_dir.glob("*"):
            if not file_path.is_file():
                continue

            try:
                mtime = file_path.stat().st_mtime
                if now - mtime > self.max_file_age_seconds:
                    file_path.unlink()
                    cleaned += 1
                    logger.info("cleaned_old_upload", file=str(file_path))
            except Exception as e:
                logger.error("cleanup_failed", file=str(file_path), error=str(e))

        logger.info("cleanup_complete", cleaned_count=cleaned)
        return cleaned

    def cleanup_temp_files(self) -> int:
        """Remove temporary files older than max_temp_file_age_seconds."""
        cleaned = 0
        now = time.time()

        for file_path in self.upload_dir.glob("tmp_*"):
            if not file_path.is_file():
                continue

            try:
                mtime = file_path.stat().st_mtime
                if now - mtime > self.max_temp_file_age_seconds:
                    file_path.unlink()
                    cleaned += 1
                    logger.info("cleaned_temp_file", file=str(file_path))
            except Exception as e:
                logger.error("temp_cleanup_failed", file=str(file_path), error=str(e))

        return cleaned

    def cleanup_orphaned_datasets(self) -> int:
        """Remove datasets that have no database record."""
        cleaned = 0

        with get_db_session() as db:
            db_dataset_ids = {ds.id for ds in db.query(DatasetModel.id).all()}

        for file_path in self.upload_dir.glob("*"):
            if not file_path.is_file():
                continue

            # Extract dataset ID from filename
            dataset_id = file_path.stem
            if dataset_id not in db_dataset_ids:
                try:
                    file_path.unlink()
                    cleaned += 1
                    logger.info("cleaned_orphaned_dataset", dataset_id=dataset_id, file=str(file_path))
                except Exception as e:
                    logger.error("orphaned_cleanup_failed", file=str(file_path), error=str(e))

        logger.info("orphaned_cleanup_complete", cleaned_count=cleaned)
        return cleaned

    def get_storage_stats(self) -> dict:
        """Get storage usage statistics."""
        if not self.upload_dir.exists():
            return {"total_files": 0, "total_size_bytes": 0, "total_size_mb": 0}

        total_files = 0
        total_size = 0

        for file_path in self.upload_dir.glob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    def run_all_cleanups(self) -> dict:
        """Run all cleanup tasks and return results."""
        results = {
            "old_uploads_cleaned": self.cleanup_old_uploads(),
            "temp_files_cleaned": self.cleanup_temp_files(),
            "orphaned_datasets_cleaned": self.cleanup_orphaned_datasets(),
            "storage_stats": self.get_storage_stats(),
        }
        logger.info("all_cleanups_complete", **results)
        return results


cleanup_service = CleanupService()