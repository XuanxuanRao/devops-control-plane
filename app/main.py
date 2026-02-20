import uuid
from datetime import datetime
from pathlib import Path
from typing import Generator
from typing import List

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import crud
from app import models
from app import schemas
from app.db import Base
from app.db import SessionLocal
from app.db import engine
from app.mq import publish_command
from app.mq import start_consumers

app = FastAPI(title="DevOps Control Plane")

static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    start_consumers()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/servers", response_model=List[schemas.ServerOut])
def list_servers(db: Session = Depends(get_db)) -> List[models.Server]:
    return crud.get_servers(db)


@app.post("/api/servers", response_model=schemas.ServerOut, status_code=status.HTTP_201_CREATED)
def create_server(server_in: schemas.ServerCreate, db: Session = Depends(get_db)) -> models.Server:
    existing = crud.get_server_by_hostname(db, server_in.hostname)
    if existing:
        raise HTTPException(status_code=409, detail="hostname already exists")
    return crud.create_server(db, server_in)


@app.get("/api/tasks", response_model=List[schemas.TaskOut])
def list_tasks(db: Session = Depends(get_db)) -> List[models.Task]:
    return crud.list_tasks(db)


@app.post("/api/commands", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_command(command_in: schemas.CommandCreate, db: Session = Depends(get_db)) -> models.Task:
    target_type = command_in.target_type
    if target_type not in {"node", "group", "all"}:
        raise HTTPException(status_code=400, detail="invalid target_type")
    routing_key = "cmd.all"
    target = command_in.target
    if target_type == "node":
        if not target:
            raise HTTPException(status_code=400, detail="target required for node")
        routing_key = f"cmd.node.{target}"
    elif target_type == "group":
        if not target:
            raise HTTPException(status_code=400, detail="target required for group")
        routing_key = f"cmd.group.{target}"

    task_id = uuid.uuid4().hex
    task = models.Task(
        task_id=task_id,
        target_type=target_type,
        target=target,
        command=command_in.command,
        timeout=command_in.timeout,
        user=command_in.user,
        status="sent",
        created_at=datetime.utcnow(),
    )
    crud.create_task(db, task)
    payload = {
        "task_id": task_id,
        "command": command_in.command,
        "timeout": command_in.timeout,
        "user": command_in.user,
        "timestamp": int(datetime.utcnow().timestamp()),
        "sign": "",
    }
    publish_command(payload, routing_key)
    return task


@app.get("/api/tasks/{task_id}/results", response_model=List[schemas.TaskResultOut])
def get_results(task_id: str, db: Session = Depends(get_db)) -> List[models.TaskResult]:
    return crud.list_task_results(db, task_id)
