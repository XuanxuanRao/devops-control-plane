import os


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://root:123456@127.0.0.1:13316/devops-control-plane",
        )
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://rabbitmq:123456@127.0.0.1:15272/")
        self.sys_cmd_exchange = os.getenv("SYS_CMD_EXCHANGE", "sys_cmd_exchange")
        self.sys_result_exchange = os.getenv("SYS_RESULT_EXCHANGE", "sys_result_exchange")
        self.sys_monitor_exchange = os.getenv("SYS_MONITOR_EXCHANGE", "sys_monitor_exchange")
        self.result_queue = os.getenv("SYS_RESULT_QUEUE", "cmd.result")
        self.status_queue = os.getenv("SYS_STATUS_QUEUE", "cmd.status")
        self.status_routing_key = os.getenv("SYS_STATUS_ROUTING_KEY", "status.node.#")
        self.monitor_queue = os.getenv("SYS_MONITOR_QUEUE", "monitor.heartbeat")
        self.heartbeat_routing_key = os.getenv("HEARTBEAT_ROUTING_KEY", "heartbeat")
        self.sign_enabled = os.getenv("SIGN_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
        self.sign_private_key_path = os.getenv("SIGN_PRIVATE_KEY_PATH", "")


settings = Settings()
