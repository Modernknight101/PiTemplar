#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request, Response
from pathlib import Path
import subprocess
import json
import time
import psutil

# Optional system_info module
try:
    import system_info
except ImportError:
    system_info = None


# ==========================================================
# App Setup
# ==========================================================
app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
AUTH_FILE = BASE_DIR / "auth.json"
CONTROL_FILE = BASE_DIR / "control.json"

SESSION_TIMEOUT = 300  # seconds
ACTIVE_USERS = {}


# ==========================================================
# Authentication
# ==========================================================
def load_auth():
    if not AUTH_FILE.exists():
        save_auth({"username": "admin", "password": "templar"})
    with open(AUTH_FILE) as f:
        return json.load(f)


def save_auth(data):
    with open(AUTH_FILE, "w") as f:
        json.dump(data, f)


def check_auth(username, password):
    auth = load_auth()
    return username == auth["username"] and password == auth["password"]


def authenticate():
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="PiTemplar Login"'}
    )


def track_user(auth):
    ACTIVE_USERS[f"{auth.username}@{request.remote_addr}"] = time.time()


def cleanup_users():
    now = time.time()
    for k, t in list(ACTIVE_USERS.items()):
        if now - t > SESSION_TIMEOUT:
            del ACTIVE_USERS[k]


def requires_auth(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        track_user(auth)
        cleanup_users()
        return f(*args, **kwargs)

    return decorated


def active_user_count():
    cleanup_users()
    return len(ACTIVE_USERS)


# ==========================================================
# Control File (Screen Flip / Invert)
# ==========================================================
def read_control():
    if not CONTROL_FILE.exists():
        return {"flip": False, "invert": False}
    try:
        with open(CONTROL_FILE) as f:
            return json.load(f)
    except:
        return {"flip": False, "invert": False}


def write_control(data):
    with open(CONTROL_FILE, "w") as f:
        json.dump(data, f)


# ==========================================================
# System Stats
# ==========================================================
def get_cpu_value():
    try:
        if system_info:
            temp = system_info.get_cpu_temp()
            if isinstance(temp, str) and temp.endswith("°C"):
                return float(temp[:-2])
            if isinstance(temp, (int, float)):
                return float(temp)
    except:
        pass
    return 0


def get_disk_info():
    try:
        if system_info:
            d = system_info.get_disk_usage()
            return {"used_percent": int(d.get("used_percent", 0))}
    except:
        pass
    return {"used_percent": 0}


def get_ram_percent():
    try:
        return int(psutil.virtual_memory().percent)
    except:
        return 0


# ==========================================================
# Routes
# ==========================================================
@app.route("/")
@requires_auth
def dashboard():
    ip = "0.0.0.0"
    try:
        if system_info:
            ip = system_info.get_ip() or ip
    except:
        pass

    return render_template(
        "dashboard.html",
        ip=ip,
        cpu=get_cpu_value(),
        disk=get_disk_info(),
        ram=get_ram_percent(),
        users=active_user_count()
    )


@app.route("/api/stats")
@requires_auth
def stats():
    return jsonify({
        "cpu": get_cpu_value(),
        "disk": get_disk_info(),
        "ram": get_ram_percent(),
        "users": active_user_count()
    })


# ==========================================================
# Password Change
# ==========================================================
@app.route("/api/change_password", methods=["POST"])
@requires_auth
def change_password():
    data = request.json
    auth = load_auth()

    if data.get("old") != auth["password"]:
        return jsonify(error="Incorrect password"), 403

    if not data.get("new"):
        return jsonify(error="New password cannot be empty"), 400

    auth["password"] = data["new"]
    save_auth(auth)
    return jsonify(ok=True)


# ==========================================================
# Screen Controls
# ==========================================================
@app.route("/api/rotate", methods=["POST"])
@requires_auth
def rotate():
    c = read_control()
    c["flip"] = not c.get("flip", False)
    write_control(c)
    return jsonify(ok=True)


@app.route("/api/invert", methods=["POST"])
@requires_auth
def invert():
    c = read_control()
    c["invert"] = not c.get("invert", False)
    write_control(c)
    return jsonify(ok=True)


# ==========================================================
# Reboot System
# ==========================================================
@app.route("/api/reboot", methods=["POST"])
@requires_auth
def reboot():
    try:
        # More reliable than plain reboot
        subprocess.Popen(["/usr/bin/sudo", "/sbin/shutdown", "-r", "now"])
        return jsonify(ok=True)
    except Exception as e:
        print("Reboot error:", e)
        return jsonify(ok=False, error=str(e)), 500


# ==========================================================
# Network
# ==========================================================
@app.route("/api/scan_networks")
@requires_auth
def scan_networks():
    try:
        result = subprocess.run(
            ["/usr/bin/nmcli", "-t", "-f", "SSID,SECURITY,SIGNAL", "dev", "wifi"],
            capture_output=True,
            text=True,
            check=True
        )

        networks = []

        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue

            parts = line.split(":")
            if len(parts) != 3:
                continue

            ssid, security, signal = parts

            networks.append({
                "ssid": ssid.strip(),
                "secure": bool(security.strip()),
                "signal": int(signal) if signal.isdigit() else 0
            })

        return jsonify(networks)

    except Exception as e:
        print("Scan error:", e)
        return jsonify([])


@app.route("/api/switch_network", methods=["POST"])
@requires_auth
def switch_network():
    data = request.json
    ssid = data.get("ssid", "").strip()
    password = data.get("password", "").strip()

    if not ssid:
        return jsonify(ok=False, error="SSID cannot be empty"), 400

    try:
        subprocess.run(
            ["/usr/bin/nmcli", "dev", "wifi", "connect", ssid, "password", password],
            check=True
        )
        return jsonify(ok=True, message=f"Connected to {ssid}")
    except subprocess.CalledProcessError:
        return jsonify(ok=False, error="Connection failed"), 500


# ==========================================================
# Run
# ==========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)