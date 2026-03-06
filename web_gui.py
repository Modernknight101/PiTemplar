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

@app.route("/api/reboot", methods=["POST"])
@requires_auth
def reboot():
    try:
        subprocess.Popen(["sudo", "/sbin/shutdown", "-r", "now"])
        return jsonify(ok=True)
    except Exception as e:
        print("Reboot error:", e)
        return jsonify(ok=False, error=str(e)), 500

# ==========================================================
# CLI inside Web GUI (sudo where allowed)
# ==========================================================
@app.route("/api/cli", methods=["POST"])
@requires_auth
def cli():
    data = request.json or {}
    cmd = data.get("command", "").strip()
    if not cmd:
        return jsonify(ok=False, error="No command provided")

    # Safe whitelist
    ALLOWED_CMDS = ["nmcli", "ifconfig", "ip", "ping", "ls", "cat", "shutdown"]
    base_cmd = cmd.split()[0]
    if base_cmd not in ALLOWED_CMDS:
        return jsonify(ok=False, error="Command not allowed")

    # Prepend sudo for privileged commands
    if base_cmd in ["nmcli", "ifconfig", "ip", "shutdown"]:
        cmd = "sudo " + cmd

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip() or result.stderr.strip()
        return jsonify(ok=True, output=output)
    except Exception as e:
        return jsonify(ok=False, error=str(e))

# ==========================================================
# Run
# ==========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)