import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

from config import settings, validate_settings


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "monitor.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("cloud_monitor")


def collect_metrics():
    """Collect local machine metrics for the monitoring demo."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(BASE_DIR.anchor or "/"))

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "local-demo",
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory.percent, 2),
        "disk_percent": round(disk.percent, 2),
    }


def evaluate_metrics(metrics):
    """Evaluate CPU, RAM, and disk metrics against configured thresholds."""
    alerts = []

    thresholds = {
        "cpu_percent": settings.cpu_threshold,
        "memory_percent": settings.ram_threshold,
        "disk_percent": settings.disk_threshold,
    }

    for metric_name, threshold in thresholds.items():
        value = metrics.get(metric_name)

        if value is not None and value >= threshold:
            alerts.append({
                "metric": metric_name,
                "value": value,
                "threshold": threshold,
                "severity": "HIGH" if value >= 95 else "WARNING",
            })

    return alerts

def run_once():
    metrics = collect_metrics()
    alerts = evaluate_metrics(metrics)

    print(json.dumps({
        "metrics": metrics,
        "alerts": alerts,
        "status": "ALERT" if alerts else "HEALTHY",
    }, indent=2))

    logger.info("METRICS %s", json.dumps(metrics))

    for alert in alerts:
        logger.warning("ALERT %s", json.dumps(alert))

    return metrics, alerts


def main():
    validate_settings()

    logger.info(
        "Monitoring started. CPU threshold=%s%%, RAM threshold=%s%%",
        settings.cpu_threshold,
        settings.ram_threshold,
    )

    try:
        while True:
            run_once()
            time.sleep(settings.check_interval)

    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user.")


if __name__ == "__main__":
    main()