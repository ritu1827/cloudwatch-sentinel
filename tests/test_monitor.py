
from monitor import evaluate_metrics
from config import settings


def test_healthy_metrics_generate_no_alerts():
    metrics = {
        "cpu_percent": 20.0,
        "memory_percent": 30.0,
        "disk_percent": 40.0,
        "timestamp": "2026-10-22T10:00:00+00:00",
        "source": "test",
    }

    alerts = evaluate_metrics(metrics)

    assert alerts == []


def test_high_cpu_generates_alert():
    metrics = {
        "cpu_percent": settings.cpu_threshold,
        "memory_percent": 30.0,
        "disk_percent": 40.0,
        "timestamp": "2026-10-22T10:00:00+00:00",
        "source": "test",
    }

    alerts = evaluate_metrics(metrics)

    assert any(
        alert["metric"] == "cpu_percent"
        for alert in alerts
    )


def test_high_memory_generates_alert():
    metrics = {
        "cpu_percent": 20.0,
        "memory_percent": settings.ram_threshold,
        "disk_percent": 40.0,
        "timestamp": "2026-10-22T10:00:00+00:00",
        "source": "test",
    }

    alerts = evaluate_metrics(metrics)

    assert any(
        alert["metric"] == "memory_percent"
        for alert in alerts
    )


def test_high_disk_generates_alert():
    metrics = {
        "cpu_percent": 20.0,
        "memory_percent": 30.0,
        "disk_percent": settings.disk_threshold,
        "timestamp": "2026-10-22T10:00:00+00:00",
        "source": "test",
    }

    alerts = evaluate_metrics(metrics)

    assert any(
        alert["metric"] == "disk_percent"
        for alert in alerts
    )
