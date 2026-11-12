from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_code: Mapped[str] = mapped_column(String(32))
    device_model: Mapped[str] = mapped_column(String(64))
    os_version: Mapped[str] = mapped_column(String(64))
    os_arch: Mapped[str] = mapped_column(String(16))
    browser_name: Mapped[str] = mapped_column(String(32))
    browser_version: Mapped[str] = mapped_column(String(32))
    user_agent: Mapped[str] = mapped_column(String(255))
    screen_resolution: Mapped[str] = mapped_column(String(32))
    color_depth: Mapped[int] = mapped_column(Integer)
    device_pixel_ratio: Mapped[int] = mapped_column(Integer)
    platform: Mapped[str] = mapped_column(String(32))
    hardware_concurrency: Mapped[int] = mapped_column(Integer)
    device_memory: Mapped[int] = mapped_column(Integer)
    touch_support: Mapped[int] = mapped_column(Integer)
    webgl_renderer: Mapped[str] = mapped_column(String(64))
    audio_context_fingerprint: Mapped[str] = mapped_column(String(32))
    canvas_fingerprint: Mapped[str] = mapped_column(String(32))
    timezone: Mapped[str] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(32))
    cookie_enabled: Mapped[int] = mapped_column(Integer)
    local_storage_enabled: Mapped[int] = mapped_column(Integer)
    webrtc_local_ip: Mapped[str] = mapped_column(String(45))
    font_list_hash: Mapped[str] = mapped_column(String(32))


class NetworkExit(Base):
    __tablename__ = "network_exits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip: Mapped[str] = mapped_column(String(45))
    ip_type: Mapped[str] = mapped_column(String(32))
    region: Mapped[str] = mapped_column(String(64))
    isp: Mapped[str] = mapped_column(String(64))
    asn: Mapped[str] = mapped_column(String(16))


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(11))
    status: Mapped[str] = mapped_column(String(16))


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reuse_intensity: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    batch_size: Mapped[int] = mapped_column(Integer)
    interval_ms: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16))
    round_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SyntheticDevice(Base):
    __tablename__ = "synthetic_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    parent_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    synthetic_code: Mapped[str] = mapped_column(String(32))
    device_model: Mapped[str] = mapped_column(String(64))
    os_version: Mapped[str] = mapped_column(String(64))
    os_arch: Mapped[str] = mapped_column(String(16))
    browser_name: Mapped[str] = mapped_column(String(32))
    browser_version: Mapped[str] = mapped_column(String(32))
    user_agent: Mapped[str] = mapped_column(String(255))
    screen_resolution: Mapped[str] = mapped_column(String(32))
    color_depth: Mapped[int] = mapped_column(Integer)
    device_pixel_ratio: Mapped[int] = mapped_column(Integer)
    platform: Mapped[str] = mapped_column(String(32))
    hardware_concurrency: Mapped[int] = mapped_column(Integer)
    device_memory: Mapped[int] = mapped_column(Integer)
    touch_support: Mapped[int] = mapped_column(Integer)
    webgl_renderer: Mapped[str] = mapped_column(String(64))
    audio_context_fingerprint: Mapped[str] = mapped_column(String(32))
    canvas_fingerprint: Mapped[str] = mapped_column(String(32))
    timezone: Mapped[str] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(32))
    cookie_enabled: Mapped[int] = mapped_column(Integer)
    local_storage_enabled: Mapped[int] = mapped_column(Integer)
    webrtc_local_ip: Mapped[str] = mapped_column(String(45))
    font_list_hash: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    synthetic_device_id: Mapped[int] = mapped_column(ForeignKey("synthetic_devices.id"))
    phone_number_id: Mapped[int] = mapped_column(ForeignKey("phone_numbers.id"))
    network_exit_id: Mapped[int] = mapped_column(ForeignKey("network_exits.id"))
    email: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    payload_json: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16))
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_source: Mapped[str] = mapped_column(String(32), default="placeholder")
    created_at: Mapped[datetime] = mapped_column(DateTime)
