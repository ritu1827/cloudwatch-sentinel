from flask import Flask, jsonify, render_template_string
from datetime import datetime, timezone

from config import settings, validate_settings
from monitor import collect_metrics, evaluate_metrics

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CloudWatch Sentinel | Monitoring</title>
    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0b1120;
            color: #e5e7eb;
        }

        header {
            padding: 24px 7%;
            background: #111827;
            border-bottom: 1px solid #263247;
        }

        header h1 { margin: 0 0 8px; font-size: 25px; }
        header p { margin: 0; color: #9ca3af; }

        main { max-width: 1100px; margin: 35px auto; padding: 0 20px; }

        .status {
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 22px;
            background: #172554;
            border: 1px solid #1d4ed8;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 18px;
        }

        .card {
            background: #111827;
            border: 1px solid #263247;
            border-radius: 12px;
            padding: 22px;
        }

        .label { color: #9ca3af; font-size: 14px; }
        .value { font-size: 32px; font-weight: bold; margin: 14px 0; }
        .bar { height: 8px; background: #263247; border-radius: 10px; overflow: hidden; }
        .fill { height: 100%; background: #38bdf8; width: 0; transition: width .3s; }
        .healthy { color: #4ade80; }
        .alert { color: #f87171; }
        .muted { color: #9ca3af; font-size: 13px; }
        button {
            padding: 11px 16px;
            margin-top: 20px;
            background: #2563eb;
            color: white;
            border: 0;
            border-radius: 7px;
            cursor: pointer;
        }
        footer { color: #9ca3af; font-size: 12px; margin-top: 25px; }

        @media (max-width: 600px) {
            header { padding: 20px; }
            .value { font-size: 28px; }
        }
    </style>
</head>
<body>
<header>
    <h1>CloudWatch Sentinel</h1>
    <p>Cloud Resource Monitoring & Alert Dashboard</p>
</header>

<main>
    <div class="status">
        <strong>System Status: </strong>
        <span id="status">Loading...</span>
        <div class="muted" id="timestamp"></div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="label">CPU Utilization</div>
            <div class="value" id="cpu">--%</div>
            <div class="bar"><div class="fill" id="cpu-bar"></div></div>
            <p class="muted">Alert threshold: <span id="cpu-threshold"></span>%</p>
        </div>

        <div class="card">
            <div class="label">Memory Utilization</div>
            <div class="value" id="ram">--%</div>
            <div class="bar"><div class="fill" id="ram-bar"></div></div>
            <p class="muted">Alert threshold: <span id="ram-threshold"></span>%</p>
        </div>

        <div class="card">
            <div class="label">Disk Utilization</div>
            <div class="value" id="disk">--%</div>
            <div class="bar"><div class="fill" id="disk-bar"></div></div>
            <p class="muted">Local machine disk usage</p>
        </div>

        <div class="card">
            <div class="label">Active Alerts</div>
            <div class="value" id="alerts">--</div>
            <p class="muted" id="alert-details">Checking metrics...</p>
        </div>
    </div>

    <button onclick="refreshMetrics()">Refresh Metrics</button>
    <footer>
        Local monitoring demo · Metrics refresh every 5 seconds ·
        Not yet connected to AWS CloudWatch
    </footer>
</main>

<script>
async function refreshMetrics() {
    try {
        const response = await fetch("/api/metrics");
        if (!response.ok) throw new Error("Unable to retrieve metrics");

        const data = await response.json();
        const m = data.metrics;
        const alerts = data.alerts;

        document.getElementById("cpu").textContent = m.cpu_percent + "%";
        document.getElementById("ram").textContent = m.memory_percent + "%";
        document.getElementById("disk").textContent = m.disk_percent + "%";

        document.getElementById("cpu-bar").style.width = m.cpu_percent + "%";
        document.getElementById("ram-bar").style.width = m.memory_percent + "%";
        document.getElementById("disk-bar").style.width = m.disk_percent + "%";

        document.getElementById("cpu-threshold").textContent = data.thresholds.cpu;
        document.getElementById("ram-threshold").textContent = data.thresholds.ram;
        document.getElementById("alerts").textContent = alerts.length;
        document.getElementById("timestamp").textContent =
            "Last updated: " + new Date(m.timestamp).toLocaleString();

        const status = document.getElementById("status");
        status.textContent = alerts.length ? "ALERT" : "HEALTHY";
        status.className = alerts.length ? "alert" : "healthy";

        document.getElementById("alert-details").textContent =
            alerts.length
                ? alerts.map(a => a.metric + ": " + a.value + "%").join(" | ")
                : "No threshold violations detected";
    } catch (error) {
        document.getElementById("status").textContent = "Monitoring unavailable";
        document.getElementById("alert-details").textContent = error.message;
    }
}

refreshMetrics();
setInterval(refreshMetrics, 5000);
</script>
</body>
</html>
"""


@app.get("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.get("/api/metrics")
def metrics_api():
    metrics = collect_metrics()
    alerts = evaluate_metrics(metrics)

    return jsonify({
        "metrics": metrics,
        "alerts": alerts,
        "thresholds": {
            "cpu": settings.cpu_threshold,
            "ram": settings.ram_threshold,
        },
        "status": "ALERT" if alerts else "HEALTHY",
    })


if __name__ == "__main__":
    validate_settings()
    app.run(host="127.0.0.1", port=5000, debug=False)