from flask import Flask, jsonify, render_template_string

from config import settings, validate_settings
from history import save_metrics, get_metrics_history
from monitor import collect_metrics, evaluate_metrics
app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CloudWatch Sentinel Pro</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
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
header h1 { margin: 0 0 8px; }
header p, .muted { color: #9ca3af; }
main { max-width: 1150px; margin: 32px auto; padding: 0 20px; }
.status, .card {
    background: #111827;
    border: 1px solid #263247;
    border-radius: 12px;
    padding: 22px;
}
.status { margin-bottom: 20px; }
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 18px;
}
.label { color: #9ca3af; font-size: 14px; }
.value { font-size: 32px; font-weight: bold; margin: 14px 0; }
.bar {
    height: 8px;
    background: #263247;
    border-radius: 10px;
    overflow: hidden;
}
.fill {
    height: 100%;
    width: 0;
    background: #38bdf8;
    transition: width .3s;
}
.healthy { color: #4ade80; }
.alert { color: #f87171; }
.muted { font-size: 13px; }
button {
    padding: 11px 16px;
    margin-top: 20px;
    background: #2563eb;
    color: white;
    border: 0;
    border-radius: 7px;
    cursor: pointer;
}
button:disabled { opacity: .6; cursor: wait; }
#alert-list { line-height: 1.8; }
footer { margin-top: 25px; color: #9ca3af; font-size: 12px; }
@media (max-width: 600px) {
    header { padding: 20px; }
    .value { font-size: 28px; }
}
</style>
</head>
<body>
<header>
    <h1>CloudWatch Sentinel Pro</h1>
    <p>System Health · Resource Monitoring · Threshold Alerts</p>
</header>

<main>
    <section class="status">
        <strong>System Status: </strong>
        <span id="status">Loading...</span>
        <div class="muted" id="timestamp">Collecting metrics...</div>
    </section>

    <section class="grid">
        <div class="card">
            <div class="label">CPU Utilization</div>
            <div class="value" id="cpu">--%</div>
            <div class="bar"><div class="fill" id="cpu-bar"></div></div>
            <p class="muted">Threshold: <span id="cpu-threshold">--</span>%</p>
        </div>

        <div class="card">
            <div class="label">Memory Utilization</div>
            <div class="value" id="ram">--%</div>
            <div class="bar"><div class="fill" id="ram-bar"></div></div>
            <p class="muted">Threshold: <span id="ram-threshold">--</span>%</p>
        </div>

        <div class="card">
            <div class="label">Disk Utilization</div>
            <div class="value" id="disk">--%</div>
            <div class="bar"><div class="fill" id="disk-bar"></div></div>
            <p class="muted">Threshold: <span id="disk-threshold">--</span>%</p>
        </div>

        <div class="card">
            <div class="label">Active Alerts</div>
            <div class="value" id="alerts">--</div>
            <p class="muted" id="alert-details">Checking metrics...</p>
        </div>
    </section>

    <section class="card" style="margin-top:20px">
        <h3>Alert Details</h3>
        <div id="alert-list" class="muted">Loading alerts...</div>
    </section>
    <section class="card" style="margin-top:20px">
        <h3>Resource Usage History</h3>
        <p class="muted">Recent CPU, memory and disk utilization</p>
        <div id="history-chart" style="width:100%; min-height:350px;">
            Loading history chart...
        </div>
    </section>
    <button id="refresh-button" onclick="refreshMetrics()">
        Refresh Metrics
    </button>

    <footer>
        Local system monitoring demo · Auto-refresh every 5 seconds
        · AWS CloudWatch integration is not enabled yet
    </footer>
</main>

<script>
async function refreshMetrics() {
    const button = document.getElementById("refresh-button");
    button.disabled = true;

    try {
        const response = await fetch("/api/metrics", { cache: "no-store" });
        if (!response.ok) throw new Error("Could not retrieve metrics");

        const data = await response.json();
        const m = data.metrics;
        const alerts = data.alerts;

        const values = [
            ["cpu", m.cpu_percent],
            ["ram", m.memory_percent],
            ["disk", m.disk_percent]
        ];

        values.forEach(([name, value]) => {
            document.getElementById(name).textContent = value + "%";
            document.getElementById(name + "-bar").style.width =
                Math.max(0, Math.min(100, value)) + "%";
        });

        document.getElementById("cpu-threshold").textContent =
            data.thresholds.cpu;
        document.getElementById("ram-threshold").textContent =
            data.thresholds.ram;
        document.getElementById("disk-threshold").textContent =
            data.thresholds.disk;
        document.getElementById("alerts").textContent = alerts.length;
        document.getElementById("timestamp").textContent =
            "Last updated: " + new Date(m.timestamp).toLocaleString();

        const status = document.getElementById("status");
        status.textContent = alerts.length ? "ALERT" : "HEALTHY";
        status.className = alerts.length ? "alert" : "healthy";

        document.getElementById("alert-details").textContent =
            alerts.length
                ? "One or more resource thresholds have been exceeded."
                : "No threshold violations detected.";

        const alertList = document.getElementById("alert-list");
        alertList.replaceChildren();

        if (alerts.length) {
            alerts.forEach(alert => {
                const item = document.createElement("div");
                item.textContent =
                    alert.metric + ": " + alert.value + "% (threshold: " +
                    alert.threshold + "%, severity: " +
                    (alert.severity || "WARNING") + ")";
                alertList.appendChild(item);
            });
        } else {
            alertList.textContent = "No active alerts. All monitored resources are within thresholds.";
        }
    } catch (error) {
        document.getElementById("status").textContent =
            "Monitoring unavailable";
        document.getElementById("status").className = "alert";
        document.getElementById("alert-details").textContent = error.message;
    } finally {
        button.disabled = false;
    }
}

refreshMetrics();
setInterval(refreshMetrics, 5000);
async function refreshHistoryChart() {
    const chart = document.getElementById("history-chart");

    try {
        const response = await fetch("/api/history", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Could not load history");
        }

        const result = await response.json();
        const history = result.history || [];

        if (history.length === 0) {
            chart.textContent = "Waiting for metrics history...";
            return;
        }

        const timestamps = history.map(item =>
            new Date(item.timestamp)
        );

        const traces = [
            {
                x: timestamps,
                y: history.map(item => item.cpu_percent),
                name: "CPU",
                type: "scatter",
                mode: "lines+markers"
            },
            {
                x: timestamps,
                y: history.map(item => item.memory_percent),
                name: "Memory",
                type: "scatter",
                mode: "lines+markers"
            },
            {
                x: timestamps,
                y: history.map(item => item.disk_percent),
                name: "Disk",
                type: "scatter",
                mode: "lines+markers"
            }
        ];

        Plotly.react(chart, traces, {
            title: "Resource Utilization Over Time",
            autosize: true,
            paper_bgcolor: "#111827",
            plot_bgcolor: "#111827",
            font: { color: "#e5e7eb" },
            xaxis: { title: "Time" },
            yaxis: {
                title: "Usage (%)",
                range: [0, 100]
            },
            legend: { orientation: "h" },
            margin: { t: 50, r: 20, b: 60, l: 55 }
        }, {
            responsive: true
        });

    } catch (error) {
        chart.textContent =
            "Chart could not load. Check your internet connection and try again.";
        console.error(error);
    }
}

refreshHistoryChart();
setInterval(refreshHistoryChart, 10000);
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

    save_metrics(metrics)

    return jsonify({
        "metrics": metrics,
        "alerts": alerts,
        "thresholds": {
            "cpu": settings.cpu_threshold,
            "ram": settings.ram_threshold,
            "disk": settings.disk_threshold,
        },
        "status": "ALERT" if alerts else "HEALTHY",
    })


@app.get("/api/history")
def history_api():
    return jsonify({
        "history": get_metrics_history(limit=50)
    })


if __name__ == "__main__":
    validate_settings()
    app.run(host="127.0.0.1", port=5000, debug=False)