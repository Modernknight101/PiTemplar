from flask import Flask, render_template, jsonify, request, Response
import json, time, subprocess
from pathlib import Path
import system_info
import psutil

# ---------------------
# App setup
# ---------------------
app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
AUTH_FILE = BASE_DIR / "auth.json"
CONTROL_FILE = BASE_DIR / "control.json"
SESSION_TIMEOUT = 300
ACTIVE_USERS = {}

# ---------------------
# Auth helpers
# ---------------------
def load_auth():
    if not AUTH_FILE.exists():
        save_auth({"username": "PiTemplar", "password": "pitemplar"})
    with open(AUTH_FILE) as f:
        return json.load(f)

def save_auth(data):
    with open(AUTH_FILE, "w") as f:
        json.dump(data, f)

def check_auth(username, password):
    auth = load_auth()
    return username == auth["username"] and password == auth["password"]

def authenticate():
    return Response("Authentication required", 401,
        {"WWW-Authenticate": 'Basic realm="TEMPLAR Login"'})

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

# ---------------------
# Control file
# ---------------------
def read_control():
    try:
        with open(CONTROL_FILE) as f:
            return json.load(f)
    except:
        return {"flip": False, "invert": False, "refresh": False}

def write_control(data):
    with open(CONTROL_FILE, "w") as f:
        json.dump(data, f)

# ---------------------
# System stats
# ---------------------
def get_cpu_percent():
    try:
        t = system_info.get_cpu_temp()
        if isinstance(t, str) and t.endswith("°C"):
            return float(t[:-2])
        if isinstance(t, (int, float)):
            return float(t)
    except:
        pass
    return 0

def get_disk_info():
    try:
        d = system_info.get_disk_usage()
        return {
            "used_percent": int(d.get("used_percent", 0))
        }
    except:
        return {"used_percent": 0}

def get_ram_percent():
    try:
        return int(psutil.virtual_memory().percent)
    except:
        return 0

# ---------------------
# Routes
# ---------------------
@app.route("/")
@requires_auth
def dashboard():
    return render_template(
        "dashboard.html",
        ip=system_info.get_ip() or "0.0.0.0",
        cpu=get_cpu_percent(),
        disk=get_disk_info(),
        ram=get_ram_percent(),
        users=active_user_count()
    )

@app.route("/api/stats")
@requires_auth
def stats():
    return jsonify({
        "cpu": get_cpu_percent(),
        "disk": get_disk_info(),
        "ram": get_ram_percent(),
        "users": active_user_count()
    })

# ---------------------
# Password
# ---------------------
@app.route("/api/change_password", methods=["POST"])
@requires_auth
def change_password():
    data = request.json
    auth = load_auth()
    if data.get("old") != auth["password"]:
        return jsonify(error="Incorrect password"), 403
    auth["password"] = data.get("new")
    save_auth(auth)
    return jsonify(ok=True)

# ---------------------
# Screen controls
# ---------------------
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

@app.route("/api/refresh", methods=["POST"])
@requires_auth
def refresh():
    c = read_control()
    c["refresh"] = True
    write_control(c)
    return jsonify(ok=True)

# ---------------------
# Network
# ---------------------
@app.route("/api/switch_network", methods=["POST"])
@requires_auth
def switch_network():
    data = request.json
    try:
        subprocess.run(
            ["sudo", "nmcli", "dev", "wifi", "connect",
             data["ssid"], "password", data["password"]],
            check=True
        )
        return jsonify(ok=True, message="Network connected")
    except subprocess.CalledProcessError as e:
        return jsonify(ok=False, error=str(e)), 500

# ---------------------
# Run
# ---------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
