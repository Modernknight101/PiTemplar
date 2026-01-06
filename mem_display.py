import sys
import os
import threading
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

import time
import shutil
import socket
import fcntl
import struct
import json

from PIL import Image, ImageDraw, ImageFont, ImageOps
from waveshare_epd import epd2in13_V4

# ---------------- CONFIG ----------------
DISK_PATH = "/"
UPDATE_INTERVAL = 900          # 15 minutes
GRAPHIC_FILE = "pik1.png"
CONTROL_FILE = "control.json"
STATE_FILE = "state.json"

# ---------------- STATE ----------------
ROTATED = False
INVERTED = False

# ---------------- FUNCTIONS ----------------
def get_ip(ifname='wlan0'):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(),
                0x8915,
                struct.pack('256s', ifname[:15].encode('utf-8'))
            )[20:24]
        )
    except:
        return "No IP"

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return f"{int(f.read()) / 1000:.1f}°C"
    except:
        return "N/A"

def get_disk_usage(path):
    d = shutil.disk_usage(path)
    used_percent = int((d.used / d.total) * 100)
    total_gb = d.total / (1024 ** 3)
    free_gb = d.free / (1024 ** 3)
    return used_percent, total_gb, free_gb

def read_control():
    try:
        with open(CONTROL_FILE, "r") as f:
            return json.load(f)
    except:
        return {"flip": False, "invert": False, "refresh": False}

def write_control(data):
    with open(CONTROL_FILE, "w") as f:
        json.dump(data, f)

# ---------------- DELAYED BOOT FLIP ----------------
def delayed_flip():
    time.sleep(7)  # wait 7 seconds after boot
    print("Flipping screen 180° after 10 seconds")

    try:
        with open(CONTROL_FILE, "r") as f:
            control = json.load(f)
    except:
        control = {"flip": False, "invert": False, "refresh": False}

    control["flip"] = True  # trigger flip
    with open(CONTROL_FILE, "w") as f:
        json.dump(control, f)

# Start delayed flip thread
threading.Thread(target=delayed_flip, daemon=True).start()

# ---------------- INIT DISPLAY ----------------
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF)

font = ImageFont.load_default()

# ---------------- LOAD GRAPHIC ----------------
if os.path.exists(GRAPHIC_FILE):
    graphic = Image.open(GRAPHIC_FILE).convert('1')
else:
    graphic = None

print("mem_display.py started")

# ---------------- MAIN LOOP ----------------
last_update = 0

while True:
    now = time.time()
    control = read_control()
    force_update = False

    # Handle flip
    if control.get("flip"):
        ROTATED = not ROTATED
        control["flip"] = False
        force_update = True

    # Handle invert
    if control.get("invert"):
        INVERTED = not INVERTED
        control["invert"] = False
        force_update = True

    # Handle refresh
    if control.get("refresh"):
        control["refresh"] = False
        force_update = True

    if force_update:
        write_control(control)

    # Update display if needed
    if force_update or (now - last_update) >= UPDATE_INTERVAL:
        last_update = now

        used_percent, total_gb, free_gb = get_disk_usage(DISK_PATH)
        ip_addr = get_ip("wlan0")
        cpu_temp = get_cpu_temp()

        # Create image
        image = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(image)

        draw.text((5, 5), "SYSTEM STATUS", font=font, fill=0)
        draw.text((5, 25), f"Disk Used: {used_percent}%", font=font, fill=0)
        draw.text((5, 40), f"Free: {free_gb:.1f} GB", font=font, fill=0)
        draw.text((5, 55), f"Total: {total_gb:.1f} GB", font=font, fill=0)
        draw.text((5, 70), f"IP: {ip_addr}", font=font, fill=0)
        draw.text((5, 85), f"CPU: {cpu_temp}", font=font, fill=0)
        draw.text((80, 35), "Sire! Log in", font=font, fill=0)
        draw.text((80, 45), "web browser", font=font, fill=0)
        draw.text((80, 55), "IP:8080", font=font, fill=0)

        if graphic:
            x = epd.height - graphic.width - 5
            image.paste(graphic, (x, 5))

        if ROTATED:
            image = image.rotate(180)

        if INVERTED:
            image = ImageOps.invert(image.convert("L")).convert("1")

        epd.display(epd.getbuffer(image))

        # Save actual screen state for GUI
        state = {"rotated": ROTATED, "inverted": INVERTED}
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

    time.sleep(1)
