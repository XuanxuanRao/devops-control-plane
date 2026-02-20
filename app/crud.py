from datetime import datetime, timezone
from typing import List
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app import schemas


def get_servers(db: Session) -> List[models.Server]:
    return list(db.execute(select(models.Server)).scalars().all())


def get_server_by_hostname(db: Session, hostname: str) -> Optional[models.Server]:
    return db.execute(select(models.Server).where(models.Server.hostname == hostname)).scalars().first()


def create_server(db: Session, server_in: schemas.ServerCreate) -> models.Server:
    server = models.Server(
        hostname=server_in.hostname,
        ip=server_in.ip,
        group=server_in.group,
        status="unknown",
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


def list_tasks(db: Session) -> List[models.Task]:
    return list(db.execute(select(models.Task).order_by(models.Task.created_at.desc())).scalars().all())


def create_task(db: Session, task: models.Task) -> models.Task:
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task_id: str, status: str) -> None:
    task = db.execute(select(models.Task).where(models.Task.task_id == task_id)).scalars().first()
    if task:
        task.status = status
        db.commit()


def create_task_result(
    db: Session,
    task_id: str,
    exit_code: Optional[int],
    stdout: Optional[str],
    stderr: Optional[str],
    timestamp: Optional[datetime],
) -> models.TaskResult:
    result = models.TaskResult(
        task_id=task_id,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        timestamp=timestamp or datetime.now(timezone.utc),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def list_task_results(db: Session, task_id: str) -> List[models.TaskResult]:
    return list(
        db.execute(select(models.TaskResult).where(models.TaskResult.task_id == task_id)).scalars().all()
    )


def update_heartbeat(
    db: Session,
    hostname: str,
    status: str,
    timestamp: datetime,
    cpu_usage: Optional[float],
    memory_usage: Optional[float],
) -> models.Server:
    server = get_server_by_hostname(db, hostname)
    if server is None:
        server = models.Server(hostname=hostname, status=status)
        db.add(server)
    server.status = status
    server.last_heartbeat = timestamp
    server.cpu_usage = cpu_usage
    server.memory_usage = memory_usage
    db.commit()
    db.refresh(server)
    return server
