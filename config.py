import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    cpu_threshold: float = float(os.getenv("CPU_THRESHOLD", "80"))
    ram_threshold: float = float(os.getenv("RAM_THRESHOLD", "80"))
    check_interval: int = int(os.getenv("CHECK_INTERVAL", "5"))
    aws_region: str = os.getenv("AWS_REGION", "ap-south-1")


settings = Settings()


def validate_settings():
    if not 0 <= settings.cpu_threshold <= 100:
        raise ValueError("CPU_THRESHOLD must be between 0 and 100.")

    if not 0 <= settings.ram_threshold <= 100:
        raise ValueError("RAM_THRESHOLD must be between 0 and 100.")

    if settings.check_interval < 1:
        raise ValueError("CHECK_INTERVAL must be at least 1 second.")