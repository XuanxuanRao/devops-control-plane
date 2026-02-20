from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ServerCreate(BaseModel):
    hostname: str
    ip: Optional[str] = None
    group: Optional[str] = None


class ServerOut(BaseModel):
    hostname: str
    ip: Optional[str]
    group: Optional[str]
    status: str
    last_heartbeat: Optional[datetime]
    cpu_usage: Optional[float]
    memory_usage: Optional[float]

    class Config:
        from_attributes = True


class CommandCreate(BaseModel):
    target_type: str
    target: Optional[str] = None
    command: str
    timeout: int = 30
    user: Optional[str] = None


class TaskOut(BaseModel):
    task_id: str
    target_type: str
    target: Optional[str]
    command: str
    timeout: int
    user: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskResultOut(BaseModel):
    task_id: str
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
