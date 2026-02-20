import os


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://root:root@127.0.0.1:3306/devops_control_plane",
        )
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/")
        self.sys_cmd_exchange = os.getenv("SYS_CMD_EXCHANGE", "sys_cmd_exchange")
        self.sys_result_exchange = os.getenv("SYS_RESULT_EXCHANGE", "sys_result_exchange")
        self.sys_monitor_exchange = os.getenv("SYS_MONITOR_EXCHANGE", "sys_monitor_exchange")
        self.result_queue = os.getenv("SYS_RESULT_QUEUE", "cmd.result")
        self.monitor_queue = os.getenv("SYS_MONITOR_QUEUE", "monitor.heartbeat")
        self.heartbeat_routing_key = os.getenv("HEARTBEAT_ROUTING_KEY", "heartbeat")


settings = Settings()
