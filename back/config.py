import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


@dataclass
class Config:
    flask_host: str = os.getenv("FLASK_HOST", "0.0.0.0")
    flask_port: int = int(os.getenv("FLASK_PORT", "5000"))
    flask_debug: bool = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "online_learning_db")

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me")
    jwt_expire_hours: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

    def __post_init__(self):
        if not self.mysql_password:
            raise RuntimeError("MYSQL_PASSWORD 未配置，请在 backend/.env 中设置 MySQL 密码")


config = Config()
