from pydantic import BaseModel, ConfigDict, Field


class TelemetryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_id: str
    pond_id: str
    timestamp: int
    temperature: float = Field(ge=-10, le=60)
    ph: float = Field(ge=0, le=14)
    do: float = Field(ge=0, le=20)
    turbidity: float = Field(ge=0, le=1000)
    data_source: str = "simulated"
    mode: str = "MOCK"
    schema_version: str = "1.0"


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    device_id: str
    pond_id: str
    mode: str
    status: str

