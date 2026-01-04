from flask import (
    Flask, jsonify, render_template_string, request, Response
)
import system_info
import json
from functools import wraps
from pathlib import Path
import time
import subprocess

# ---------------------
# APP SETUP
# ---------------------
app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
AUTH_FILE = BASE_DIR / "auth.json"
CONTROL_FILE = BASE_DIR / "control.json"
PITEMPLAR_ROOT = Path("/home/templar/PITEMPLAR").resolve()

SESSION_TIMEOUT = 300
ACTIVE_USERS = {}

# ---------------------
# AUTH STORAGE
# ---------------------
def load_auth():
    if not AUTH_FILE.exists():
        save_auth({"username": "templar", "password": "templar"})
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
        {"WWW-Authenticate": 'Basic realm="PITEMPLAR Login"'}
    )

def track_user(auth):
    key = f"{auth.username}@{request.remote_addr}"
    ACTIVE_USERS[key] = time.time()

def cleanup_users():
    now = time.time()
    for k, t in list(ACTIVE_USERS.items()):
        if now - t > SESSION_TIMEOUT:
            del ACTIVE_USERS[k]

def requires_auth(f):
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
# CONTROL FILE
# ---------------------
def read_control():
    try:
        with open(CONTROL_FILE) as f:
            return json.load(f)
    except Exception:
        return {"flip": False, "invert": False, "refresh": False}

def write_control(data):
    with open(CONTROL_FILE, "w") as f:
        json.dump(data, f)

# ---------------------
# DASHBOARD HTML
# ---------------------
DASHBOARD_HTML = """
<!doctype html>
<title>PITEMPLAR Control</title>
<style>
body { font-family: sans-serif; background:#111; color:#eee; padding:20px }
.card { background:#222; padding:15px; border-radius:8px; max-width:420px }
button { width: 100%; margin-top: 8px; padding: 8px; font-size: 14px; background: #333; color: #eee; border: none; border-radius: 5px; cursor: pointer;}
button:hover { background:#444 }
input { width:100%; margin-top:6px; padding:6px }
a { color:#7fc7ff; text-decoration:none }
</style>

<div class="card">
  <h2>System Status</h2>
  <p><b>IP:</b> {{ ip }}</p>
  <p><b>Disk:</b> {{ disk.used_percent }}%</p>
  <p><b>Free:</b> {{ disk.free_gb }} GB</p>
  <p><b>Total:</b> {{ disk.total_gb }} GB</p>
  <p><b>CPU:</b> {{ cpu }}</p>
  <p><b>Active Users:</b> {{ users }}</p>

  <button onclick="post('/api/rotate')">Rotate Screen 180°</button>
  <button onclick="post('/api/invert')">Invert Screen</button>
  <button onclick="post('/api/refresh')">Refresh Screen</button>

  <hr>
  <h3>Upload to PITEMPLAR</h3>
  <input type="file" id="fileInput">
  <button onclick="startUpload()">Upload</button>
  <p id="status"></p>

  <hr>
  <h3>Change Password</h3>
  <input type="password" id="oldpw" placeholder="Current password">
  <input type="password" id="newpw" placeholder="New password">
  <button onclick="changePassword()">Change Password</button>
  <p id="pwstatus"></p>

  <hr>
  <h3>Switch Network</h3>
  <input type="text" id="ssid" placeholder="SSID">
  <input type="password" id="netpw" placeholder="Password">
  <button onclick="switchNetwork()">Connect</button>
  <p id="netstatus"></p>

  <hr>
  <a href="/browse"><button>Browse PITEMPLAR</button></a>
</div>

<script>
function post(url) { fetch(url, {method:"POST"}); }

const CHUNK_SIZE = 10 * 1024 * 1024;

async function startUpload() {
  const file = document.getElementById("fileInput").files[0];
  if (!file) return alert("Select a file");

  const status = document.getElementById("status");
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

  for (let i = 0; i < totalChunks; i++) {
    const chunk = file.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE);

    const form = new FormData();
    form.append("file", chunk);
    form.append("filename", file.name);
    form.append("index", i);
    form.append("total", totalChunks);

    const resp = await fetch("/api/upload_chunk", {
      method: "POST",
      body: form
    });

    if (!resp.ok) {
      status.textContent = "Upload failed";
      return;
    }

    status.textContent =
      "Uploading: " + Math.round((i + 1) / totalChunks * 100) + "%";
  }

  status.textContent = "Upload complete!";
}

async function changePassword() {
  const resp = await fetch("/api/change_password", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      old: oldpw.value,
      new: newpw.value
    })
  });

  pwstatus.textContent = resp.ok ? "Password updated" : "Password change failed";
}

async function switchNetwork() {
  const resp = await fetch("/api/switch_network", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      ssid: ssid.value,
      password: netpw.value
    })
  });

  const data = await resp.json();
  netstatus.textContent = data.ok ? data.message : data.error;
}
</script>
"""

# ---------------------
# DASHBOARD ROUTE
# ---------------------
@app.route("/")
@requires_auth
def dashboard():
    return render_template_string(
        DASHBOARD_HTML,
        ip=system_info.get_ip(),
        cpu=system_info.get_cpu_temp(),
        disk=system_info.get_disk_usage(),
        users=active_user_count()
    )

# ---------------------
# PASSWORD CHANGE API
# ---------------------
@app.route("/api/change_password", methods=["POST"])
@requires_auth
def change_password():
    data = request.json
    old = data.get("old")
    new = data.get("new")

    auth = load_auth()

    if old != auth["password"]:
        return jsonify(error="Old password incorrect"), 403

    if not new or len(new) < 6:
        return jsonify(error="Password too short"), 400

    auth["password"] = new
    save_auth(auth)
    return jsonify(ok=True)

# ---------------------
# CONTROL API
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
# NETWORK SWITCHING API
# ---------------------
@app.route("/api/switch_network", methods=["POST"])
@requires_auth
def switch_network():
    data = request.json
    ssid = data.get("ssid")
    password = data.get("password")
    if not ssid or not password:
        return jsonify(ok=False, error="SSID and password required"), 400

    try:
        # List all saved Wi-Fi connections
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show"],
            capture_output=True, text=True, check=True
        )

        connections = {}
        for line in result.stdout.splitlines():
            name, type_, device = line.split(":")
            if type_ == "wifi":
                connections[name] = device

        # Bring up the connection if it exists
        if ssid in connections:
            subprocess.run(["sudo", "nmcli", "connection", "up", ssid], check=True)
        else:
            # Create and connect a new Wi-Fi connection
            subprocess.run(
                ["sudo", "nmcli", "dev", "wifi", "connect", ssid, "password", password],
                check=True
            )

        # Delete all other saved Wi-Fi connections
        for name in connections:
            if name != ssid:
                subprocess.run(["sudo", "nmcli", "connection", "delete", name])

        return jsonify(ok=True, message=f"Connected to '{ssid}'")
    except subprocess.CalledProcessError as e:
        return jsonify(ok=False, error=str(e)), 500

# ---------------------
# FILE MANAGER MODULE
# ---------------------
from file_manager import register_file_manager
register_file_manager(app, requires_auth, PITEMPLAR_ROOT)

# ---------------------
# MAIN
# ---------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
