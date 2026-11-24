import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.flagsmith import (
    FlagsmithConnectionType,
    FlagsmithConnectionStatus,
    SyncStatus,
    SyncTrigger,
)
from app.models.feature_flag import FeatureFlagType


class FlagsmithTestConnectionRequest(BaseModel):
    api_url: str = Field(..., min_length=4)
    token: str = Field(..., min_length=4)
    connection_type: FlagsmithConnectionType = FlagsmithConnectionType.CLOUD


class FlagsmithTestConnectionResponse(BaseModel):
    ok: bool
    message: str
    projects_count: int = 0
    latency_ms: float = 0.0


class FlagsmithConnectionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    api_url: str = Field(..., min_length=4)
    token: str = Field(..., min_length=4)
    connection_type: FlagsmithConnectionType = FlagsmithConnectionType.CLOUD
    webhook_secret: Optional[str] = None


class FlagsmithConnectionUpdate(BaseModel):
    name: Optional[str] = None
    api_url: Optional[str] = None
    token: Optional[str] = None
    webhook_secret: Optional[str] = None


class FlagsmithConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    api_url: str
    connection_type: FlagsmithConnectionType
    status: FlagsmithConnectionStatus
    has_token: bool = True
    has_webhook_secret: bool = False
    last_synced_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime


class SyncHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    connection_id: uuid.UUID
    status: SyncStatus
    trigger: SyncTrigger
    records_created: int
    records_updated: int
    records_unchanged: int
    records_deleted: int
    error_details: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class FeatureFlagStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    environment_id: uuid.UUID
    environment_name: Optional[str] = None
    is_production: bool = False
    enabled: bool
    value: Optional[str] = None


class FeatureFlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    project_name: Optional[str] = None
    flagsmith_feature_id: Optional[str] = None
    name: str
    key: str
    description: Optional[str] = None
    type: FeatureFlagType
    default_enabled: bool
    is_archived: bool
    states: List[FeatureFlagStateOut] = []
    updated_at: datetime
