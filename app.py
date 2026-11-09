from flask import Flask, render_template, jsonify
import psutil
import socket
import platform
import time
from datetime import datetime

app = Flask(__name__)

BOOT_TIME = psutil.boot_time()
START_TIME = time.time()

previous_network = psutil.net_io_counters()
previous_time = time.time()


def get_ip():
    addresses = psutil.net_if_addrs()

    for interface, values in addresses.items():
        if interface == "en0":
            for value in values:
                if value.family == socket.AF_INET:
                    return value.address

    return "Not found"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/stats")
def stats():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    network = psutil.net_io_counters()

    global previous_network, previous_time

    current_time = time.time()
    elapsed = max(current_time - previous_time, 0.001)

    upload = (network.bytes_sent - previous_network.bytes_sent) / elapsed
    download = (network.bytes_recv - previous_network.bytes_recv) / elapsed

    previous_network = network
    previous_time = current_time

    return jsonify({
        "cpu": psutil.cpu_percent(interval=None),
        "ram": memory.percent,
        "ram_used": round(memory.used / 1024**3, 1),
        "ram_total": round(memory.total / 1024**3, 1),
        "disk": disk.percent,
        "disk_free": round(disk.free / 1024**3, 1),
        "ip": get_ip(),
        "uptime": int(time.time() - BOOT_TIME),
        "upload": round(upload / 1024, 1),
        "download": round(download / 1024, 1),
        "network_sent": round(network.bytes_sent / 1024**3, 2),
        "network_received": round(network.bytes_recv / 1024**3, 2),
        "process_count": len(psutil.pids()),
        "hostname": socket.gethostname()
    })


@app.route("/api/processes")
def processes():
    result = []

    for process in psutil.process_iter(
        ["pid", "name", "memory_percent", "cpu_percent"]
    ):
        try:
            result.append(process.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    result.sort(
        key=lambda item: item["memory_percent"] or 0,
        reverse=True
    )

    return jsonify(result[:15])


@app.route("/api/system")
def system():
    return jsonify({
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "hostname": socket.gethostname(),
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "boot_time": datetime.fromtimestamp(
            BOOT_TIME
        ).strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "online",
        "uptime": round(time.time() - START_TIME),
        "time": datetime.now().strftime("%H:%M:%S")
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5050,
        debug=False
    )
