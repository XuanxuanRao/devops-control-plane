import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any
from typing import Dict

import pika

from app.config import settings
from app.mq_handlers import handle_heartbeat_message
from app.mq_handlers import handle_result_message
from app.mq_handlers import handle_status_message
from app.util.sign_util import RSASigner

signer = RSASigner(
    private_key_path=settings.sign_private_key_path,
    enabled=settings.sign_enabled,
)

logger = logging.getLogger(__name__)


def publish_command(payload: Dict[str, Any], routing_key: str) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()
    channel.exchange_declare(exchange=settings.sys_cmd_exchange, exchange_type="topic", durable=True)
    
    timestamp = int(datetime.now(timezone.utc).timestamp())
    
    hostname = payload.get("hostname", "aliyun_linux_2g")
    sign_data = {
        "hostname": hostname,
        "timestamp": timestamp
    }
    
    signature = signer.sign(sign_data)
    
    if not signature:
        logging.error("Failed to sign message")
    
    headers = {
        "x-signature": signature,
        "x-timestamp": timestamp
    }
    
    channel.basic_publish(
        exchange=settings.sys_cmd_exchange,
        routing_key=routing_key,
        body=json.dumps(payload).encode("utf-8"),
        properties=pika.BasicProperties(
            delivery_mode=2,
            headers=headers
        ),
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
                try:
                    handle_result_message(body, properties)
                except Exception:
                    logger.exception("result_message_handler_error")
                finally:
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
                try:
                    handle_heartbeat_message(body, properties)
                except Exception:
                    logger.exception("heartbeat_message_handler_error")
                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=settings.monitor_queue, on_message_callback=callback)
            channel.start_consuming()
        except Exception:
            logger.exception("heartbeat_consumer_error")
            time.sleep(3)


def _consume_status() -> None:
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
            channel = connection.channel()
            channel.exchange_declare(exchange=settings.sys_result_exchange, exchange_type="topic", durable=True)
            channel.queue_declare(queue=settings.status_queue, durable=True)
            channel.queue_bind(
                queue=settings.status_queue,
                exchange=settings.sys_result_exchange,
                routing_key=settings.status_routing_key,
            )

            def callback(ch, method, properties, body) -> None:
                try:
                    handle_status_message(body, properties)
                except Exception:
                    logger.exception("status_message_handler_error")
                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=settings.status_queue, on_message_callback=callback)
            channel.start_consuming()
        except Exception:
            logger.exception("status_consumer_error")
            time.sleep(3)


def start_consumers() -> None:
    threading.Thread(target=_consume_results, daemon=True).start()
    threading.Thread(target=_consume_heartbeat, daemon=True).start()
    threading.Thread(target=_consume_status, daemon=True).start()
