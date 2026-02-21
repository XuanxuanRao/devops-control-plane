import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app import crud
from app.config import settings
from app.db import SessionLocal
from app.security.public_key_store import PublicKeyStore
from app.util.sign_util import verify_with_public_key

logger = logging.getLogger(__name__)

public_key_store = PublicKeyStore()


def _decode_json(body: bytes) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(body.decode("utf-8"))
    except Exception as exc:
        logger.error(f"Error decoding message body: {exc}")
        return None


def _verify_message_if_needed(
    data: Dict[str, Any],
    properties: Any,
    failure_log: str,
) -> bool:
    headers = properties.headers if properties and properties.headers else {}
    signature = headers.get("x-signature", "")
    header_timestamp = headers.get("x-timestamp", 0)
    if not (signature and header_timestamp):
        return True
    hostname = data.get("hostname", "")
    verify_data = {
        "hostname": hostname,
        "timestamp": header_timestamp,
    }
    with SessionLocal() as db:
        public_key = public_key_store.get_public_key(db, hostname)
    verified = verify_with_public_key(
        verify_data,
        signature,
        public_key,
        settings.sign_enabled,
    )
    if not verified:
        logger.error(failure_log)
    return verified


def handle_result_message(body: bytes, properties: Any) -> bool:
    data = _decode_json(body)
    if not data:
        return False
    if not _verify_message_if_needed(data, properties, "Failed to verify message signature"):
        return False
    try:
        task_id = data.get("task_id")
        exit_code = data.get("exit_code")
        stdout = data.get("stdout")
        stderr = data.get("stderr")
        ts = data.get("timestamp")
        timestamp = datetime.fromtimestamp(ts, timezone.utc) if isinstance(ts, (int, float)) else datetime.now(timezone.utc)
        if task_id:
            with SessionLocal() as db:
                crud.create_task_result(db, task_id, exit_code, stdout, stderr, timestamp)
                crud.update_task_status(db, task_id, "done")
    except Exception as exc:
        logger.error(f"Error processing result message: {exc}")
        return False
    return True


def handle_heartbeat_message(body: bytes, properties: Any) -> bool:
    data = _decode_json(body)
    if not data:
        return False
    if not _verify_message_if_needed(data, properties, "Failed to verify heartbeat message signature"):
        return False
    try:
        hostname = data.get("hostname")
        status = data.get("status", "unknown")
        ts = data.get("timestamp")
        cpu_usage = data.get("cpu_usage")
        memory_usage = data.get("mem_usage")
        timestamp = datetime.fromtimestamp(ts, timezone.utc) if isinstance(ts, (int, float)) else datetime.now(timezone.utc)
        if hostname:
            with SessionLocal() as db:
                crud.update_heartbeat(db, hostname, status, timestamp, cpu_usage, memory_usage)
    except Exception as exc:
        logger.error(f"Error processing heartbeat message: {exc}")
        return False
    return True


def handle_status_message(body: bytes, properties: Any) -> bool:
    data = _decode_json(body)
    if not data:
        return False
    if not _verify_message_if_needed(data, properties, "Failed to verify status message signature"):
        return False
    try:
        task_id = data.get("task_id") or data.get("taskID")
        status = data.get("status")
        reason = data.get("reason")
        if not task_id or not status:
            logger.error("Missing task_id or status in status message")
            return False
        allowed_statuses = {"pending", "received", "rejected", "done"}
        if status not in allowed_statuses:
            logger.error(f"Invalid status value: {status}")
            return False
        with SessionLocal() as db:
            task = crud.get_task_by_id(db, task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False
            current_status = task.status or "pending"
            if current_status == status:
                return True
            transitions = {
                "pending": {"received", "rejected"},
                "received": {"done", "rejected"},
                "rejected": set(),
                "done": set(),
            }
            if status not in transitions.get(current_status, set()):
                logger.error(f"Invalid status transition: {current_status} -> {status}")
                return False
            crud.update_task_status(db, task_id, status)
        if status == "rejected" and reason:
            logger.info(f"Task {task_id} rejected: {reason}")
    except Exception as exc:
        logger.error(f"Error processing status message: {exc}")
        return False
    return True
