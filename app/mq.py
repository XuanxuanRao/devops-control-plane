import json
import logging
import threading
import time
from datetime import datetime
from typing import Any
from typing import Dict

import pika

from app import crud
from app.config import settings
from app.db import SessionLocal

logger = logging.getLogger(__name__)


def publish_command(payload: Dict[str, Any], routing_key: str) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()
    channel.exchange_declare(exchange=settings.sys_cmd_exchange, exchange_type="topic", durable=True)
    channel.basic_publish(
        exchange=settings.sys_cmd_exchange,
        routing_key=routing_key,
        body=json.dumps(payload).encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


def _consume_results() -> None:
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
            channel = connection.channel()
            channel.exchange_declare(exchange=settings.sys_result_exchange, exchange_type="topic", durable=True)
            channel.queue_declare(queue=settings.result_queue, durable=True)
            channel.queue_bind(queue=settings.result_queue, exchange=settings.sys_result_exchange, routing_key="result.#")

            def callback(ch, method, properties, body) -> None:
                data = json.loads(body.decode("utf-8"))
                task_id = data.get("task_id")
                exit_code = data.get("exit_code")
                stdout = data.get("stdout")
                stderr = data.get("stderr")
                ts = data.get("timestamp")
                timestamp = datetime.utcfromtimestamp(ts) if isinstance(ts, (int, float)) else datetime.utcnow()
                with SessionLocal() as db:
                    if task_id:
                        crud.create_task_result(db, task_id, exit_code, stdout, stderr, timestamp)
                        crud.update_task_status(db, task_id, "done")
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=settings.result_queue, on_message_callback=callback)
            channel.start_consuming()
        except Exception:
            logger.exception("result_consumer_error")
            time.sleep(3)


def _consume_heartbeat() -> None:
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
            channel = connection.channel()
            channel.exchange_declare(exchange=settings.sys_monitor_exchange, exchange_type="topic", durable=True)
            channel.queue_declare(queue=settings.monitor_queue, durable=True)
            channel.queue_bind(
                queue=settings.monitor_queue,
                exchange=settings.sys_monitor_exchange,
                routing_key=settings.heartbeat_routing_key,
            )

            def callback(ch, method, properties, body) -> None:
                data = json.loads(body.decode("utf-8"))
                print("get heartbeat:", data)
                hostname = data.get("hostname")
                status = data.get("status", "unknown")
                ts = data.get("timestamp")
                cpu_usage = data.get("cpu_usage")
                memory_usage = data.get("mem_usage")
                timestamp = datetime.utcfromtimestamp(ts) if isinstance(ts, (int, float)) else datetime.utcnow()
                if hostname:
                    with SessionLocal() as db:
                        crud.update_heartbeat(db, hostname, status, timestamp, cpu_usage, memory_usage)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=settings.monitor_queue, on_message_callback=callback)
            channel.start_consuming()
        except Exception:
            logger.exception("heartbeat_consumer_error")
            time.sleep(3)


def start_consumers() -> None:
    threading.Thread(target=_consume_results, daemon=True).start()
    threading.Thread(target=_consume_heartbeat, daemon=True).start()
