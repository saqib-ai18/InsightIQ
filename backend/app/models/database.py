from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from uuid import uuid4

Base = declarative_base()


def gen_uuid():
    return str(uuid4())


class DatasetModel(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    columns = Column(JSON, nullable=True)
    missing_values = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    quality_score = Column(Integer, default=100)
    status = Column(String(50), default="READY")
    sheet_name = Column(String(255), nullable=True)
    encoding = Column(String(50), nullable=True)
    delimiter = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    file_path = Column(String(500), nullable=True)

    charts = relationship("ChartModel", back_populates="dataset", cascade="all, delete-orphan")
    dashboards = relationship("DashboardModel", back_populates="dataset", cascade="all, delete-orphan")
    reports = relationship("ReportModel", back_populates="dataset", cascade="all, delete-orphan")


class ChartModel(Base):
    __tablename__ = "charts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(255), nullable=False)
    chart_type = Column(String(50), nullable=False)
    config = Column(JSON, nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("DatasetModel", back_populates="charts")


class DashboardModel(Base):
    __tablename__ = "dashboards"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    widgets = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("DatasetModel", back_populates="dashboards")


class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    template = Column(String(50), default="custom")
    format = Column(String(20), default="pdf")
    config = Column(JSON, nullable=True, default=dict)
    status = Column(String(50), default="pending")
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    dataset = relationship("DatasetModel", back_populates="reports")


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class APIKeyModel(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    prefix = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)