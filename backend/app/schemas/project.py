import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class EnvironmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    is_production: bool = False
    flagsmith_environment_key: Optional[str] = None


class EnvironmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    slug: str
    is_production: bool
    flagsmith_environment_key: Optional[str] = None
    created_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = None
    description: str = ""
    flagsmith_project_id: Optional[str] = None
    create_default_environments: bool = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    flagsmith_project_id: Optional[str] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    description: str
    flagsmith_project_id: Optional[str] = None
    environments: List[EnvironmentOut] = []
    created_at: datetime
