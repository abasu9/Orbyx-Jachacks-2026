from datetime import date
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    level: Optional[str] = None
    apr: Optional[Dict[str, Any]] = None
    pip: int = 0
    joiningdate: date
    gh_username: Optional[str] = None
    ranking: Optional[float] = None
    roi: Optional[float] = None
    report_id: Optional[str] = None

class UserCreate(BaseModel):
    name: str
    level: Optional[str] = None
    apr: Optional[Dict[str, Any]] = None
    pip: int = 0
    joiningdate: date
    gh_username: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    apr: Optional[Dict[str, Any]] = None
    pip: Optional[int] = None
    joiningdate: Optional[date] = None
    gh_username: Optional[str] = None
    ranking: Optional[float] = None
    roi: Optional[float] = None
    report_id: Optional[str] = None

class User(UserBase):
    id: UUID

    class Config:
        from_attributes = True
