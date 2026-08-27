from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="operator")


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    pond_id: Mapped[str] = mapped_column(String(64), index=True)
    mode: Mapped[str] = mapped_column(String(8), default="MOCK")
    status: Mapped[str] = mapped_column(String(32), default="OFFLINE")
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SensorData(Base):
    __tablename__ = "sensor_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), index=True)
    pond_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[int] = mapped_column(Integer, index=True)
    temperature: Mapped[float] = mapped_column(Float)
    ph: Mapped[float] = mapped_column(Float)
    do: Mapped[float] = mapped_column(Float)
    turbidity: Mapped[float] = mapped_column(Float)
    data_source: Mapped[str] = mapped_column(String(16), default="simulated")
    mode: Mapped[str] = mapped_column(String(8), default="MOCK")
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0")
    __table_args__ = (Index("ix_sensor_data_pond_time", "pond_id", "timestamp"),)


class Alarm(Base):
    __tablename__ = "alarms"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    pond_id: Mapped[str] = mapped_column(String(64), index=True)
    level: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)


class OxygenMachine(Base):
    __tablename__ = "oxygen_machines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    pond_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="OFF")
    mode: Mapped[str] = mapped_column(String(16), default="AUTO")
    last_transition_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_command_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manual_override: Mapped[bool] = mapped_column(Boolean, default=False)
    emergency_stop: Mapped[bool] = mapped_column(Boolean, default=False)


class ControlLog(Base):
    __tablename__ = "control_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_id: Mapped[str] = mapped_column(String(64), index=True)
    operator: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(Text)
    result: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pond_id: Mapped[str] = mapped_column(String(64), index=True)
    risk_level: Mapped[str] = mapped_column(String(16))
    probability: Mapped[float] = mapped_column(Float)
    horizon_minutes: Mapped[int] = mapped_column(Integer)
    data_source: Mapped[str] = mapped_column(String(16), default="simulated")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DeviceStatus(Base):
    __tablename__ = "device_status"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SensorCalibration(Base):
    __tablename__ = "sensor_calibrations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    sensor_type: Mapped[str] = mapped_column(String(32))
    offset: Mapped[float] = mapped_column(Float, default=0.0)
    scale: Mapped[float] = mapped_column(Float, default=1.0)
