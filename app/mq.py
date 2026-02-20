import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any
from typing import Dict

import pika

from app import crud
from app.config import settings
from app.db import SessionLocal
from app.util.sign_util import RSASigner

# Initialize message signer using sign_util
signer = RSASigner(
    private_key_path="/Users/rcx/code/python/devops-control-plane/private.pem",
    public_key_path="/Users/rcx/code/python/devops-control-plane/public-agent.pem",
    enabled=True
)

logger = logging.getLogger(__name__)


def publish_command(payload: Dict[str, Any], routing_key: str) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()
    channel.exchange_declare(exchange=settings.sys_cmd_exchange, exchange_type="topic", durable=True)
    
    # Generate timestamp
    timestamp = int(datetime.now(timezone.utc).timestamp())
    
    # Prepare data for signing - only use hostname and timestamp
    hostname = payload.get('hostname', 'aliyun_linux_2g')
    sign_data = {
        "hostname": hostname,
        "timestamp": timestamp
    }
    
    # Sign the data
    signature = signer.sign(sign_data)
    
    if not signature:
        logging.error("Failed to sign message")
    
    # Add signature and timestamp headers
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
                # Read signature and timestamp headers
                signature = properties.headers.get("x-signature", "") if properties.headers else ""
                header_timestamp = properties.headers.get("x-timestamp", 0) if properties.headers else 0
                
                # Verify message signature
                if signature and header_timestamp:
                    try:
                        # Parse message to get hostname
                        message_data = json.loads(body.decode("utf-8"))
                        hostname = message_data.get('hostname', '')
                        
                        # Prepare data for verification - only use hostname and timestamp
                        verify_data = {
                            "hostname": hostname,
                            "timestamp": header_timestamp
                        }
                        
                        # Verify the signature
                        verified = signer.verify(verify_data, signature)
                        
                        if not verified:
                            logging.error("Failed to verify message signature")
                            # Acknowledge but don't process invalid messages
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            return
                    except Exception as e:
                        logging.error(f"Error during signature verification: {e}")
                        # Acknowledge but don't process invalid messages
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return
                
                try:
                    # Parse message
                    data = json.loads(body.decode("utf-8"))
                    
                    task_id = data.get("task_id")
                    exit_code = data.get("exit_code")
                    stdout = data.get("stdout")
                    stderr = data.get("stderr")
                    ts = data.get("timestamp")
                    timestamp = datetime.fromtimestamp(ts, timezone.utc) if isinstance(ts, (int, float)) else datetime.now(timezone.utc)
                    
                    with SessionLocal() as db:
                        if task_id:
                            crud.create_task_result(db, task_id, exit_code, stdout, stderr, timestamp)
                            crud.update_task_status(db, task_id, "done")
                except Exception as e:
                    logging.error(f"Error processing result message: {e}")
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
                # Read signature and timestamp headers
                signature = properties.headers.get("x-signature", "") if properties.headers else ""
                header_timestamp = properties.headers.get("x-timestamp", 0) if properties.headers else 0
                
                # Verify message signature
                if signature and header_timestamp:
                    try:
                        # Parse message to get hostname
                        message_data = json.loads(body.decode("utf-8"))
                        hostname = message_data.get('hostname', '')
                        
                        # Prepare data for verification - only use hostname and timestamp
                        verify_data = {
                            "hostname": hostname,
                            "timestamp": header_timestamp
                        }
                        
                        # Verify the signature
                        verified = signer.verify(verify_data, signature)
                        
                        if not verified:
                            logging.error("Failed to verify heartbeat message signature")
                            # Acknowledge but don't process invalid messages
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            return
                    except Exception as e:
                        logging.error(f"Error during heartbeat signature verification: {e}")
                        # Acknowledge but don't process invalid messages
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return
                
                try:
                    # Parse message
                    data = json.loads(body.decode("utf-8"))
                    
                    hostname = data.get("hostname")
                    status = data.get("status", "unknown")
                    ts = data.get("timestamp")
                    cpu_usage = data.get("cpu_usage")
                    memory_usage = data.get("mem_usage")
                    timestamp = datetime.fromtimestamp(ts, timezone.utc) if isinstance(ts, (int, float)) else datetime.now(timezone.utc)
                    
                    if hostname:
                        with SessionLocal() as db:
                            crud.update_heartbeat(db, hostname, status, timestamp, cpu_usage, memory_usage)
                except Exception as e:
                    logging.error(f"Error processing heartbeat message: {e}")
                finally:
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
