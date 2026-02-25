#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import threading
import time
import shutil
import socket
import fcntl
import struct
import json
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ---------------- ADD LIB TO PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "lib"))
sys.path.append(LIB_DIR)

from waveshare_epd import epd2in13_V4  # change to epd4in2_V2 if needed

# ---------------- CONFIG ----------------
DISK_PATH = "/"
CONTROL_FILE = "control.json"
STATE_FILE = "state.json"

GRAPHIC_PREFIX = "pik"
GRAPHIC_COUNT = 10
INTERVAL = 7  # seconds

PHRASES = [
    ("Sire! Log in via thy browser!", "Thy IP and port 8080"),
    ("Sire! Thy IP and THY port!", "They shall show the way!"),
    ("Sire! IP:8080 login My liege!", "Command thy legion!"),
    ("Sire, Thy share \\\\IP\\private", "I shall keep thy data safe!"),
    ("I am PiTemplar sire!", "Data Bank is my sacred duty!"),
    ("Guard thy bits, my liege!", "The vault stands ready!"),
    ("Thy server awakens!", "8080 awaits thy command!"),
    ("Sire! Network stands firm!", "No packets shall falter!"),
    ("I watch thy disks, sire!", "Not a byte goes astray!"),
    ("Rest easy, my liege!", "PiTemplar stands watch!")
]

# ---------------- STATE ----------------
ROTATED = False
INVERTED = False
GRAPHIC_INDEX = 8  # start at pik8.png

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
    return used_percent

def get_ssid():
    try:
        ssid = os.popen("iwgetid -r").read().strip()
        return ssid if ssid else "No WiFi"
    except:
        return "No WiFi"

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
    time.sleep(7)
    control = read_control()
    control["flip"] = True
    write_control(control)

threading.Thread(target=delayed_flip, daemon=True).start()

# ---------------- INIT DISPLAY ----------------
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF)

# Fonts
font = ImageFont.load_default()
try:
    title_font = ImageFont.truetype("fonts/PirataOne-Regular.ttf", 22)
except:
    title_font = font

# Load graphics at original size
graphics = []
for i in range(GRAPHIC_COUNT):
    filename = f"{GRAPHIC_PREFIX}{i}.png"
    if os.path.exists(filename):
        graphics.append(Image.open(filename).convert("1"))
    else:
        graphics.append(None)

print("mem_display_partial.py started (Pirata One title + system info)")

# ---------------- MAIN LOOP ----------------
while True:
    control = read_control()
    force_update = False

    if control.get("flip"):
        ROTATED = not ROTATED
        control["flip"] = False
        force_update = True

    if control.get("invert"):
        INVERTED = not INVERTED
        control["invert"] = False
        force_update = True

    if control.get("refresh"):
        control["refresh"] = False
        force_update = True

    if force_update:
        write_control(control)

    # ---------------- UPDATE DISPLAY ----------------
    GRAPHIC_INDEX = (GRAPHIC_INDEX + 1) % GRAPHIC_COUNT

    used_percent = get_disk_usage(DISK_PATH)
    ssid = get_ssid()
    ip_addr = get_ip("wlan0")
    cpu_temp = get_cpu_temp()

    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    # Title
    draw.text((5, 5), "PiTemplar", font=title_font, fill=0)
    draw.line((5, 30, epd.height - 5, 30), fill=0)

    # Phrases
    line1, line2 = PHRASES[GRAPHIC_INDEX]
    draw.text((5, 35), line1, font=font, fill=0)
    draw.text((5, 48), line2, font=font, fill=0)

    # System info
    draw.text((5, 50), "_____________________________", font=font, fill=0)
    draw.text((5, 68), f"Disk Used: {used_percent}%", font=font, fill=0)
    draw.text((5, 83), f"WiFi: {ssid}", font=font, fill=0)
    draw.text((5, 97), f"IP: {ip_addr}", font=font, fill=0)
    draw.text((5, 110), f"CPU: {cpu_temp}", font=font, fill=0)

    # Graphic at original size/position
    current_graphic = graphics[GRAPHIC_INDEX]
    if current_graphic:
        x = epd.height - current_graphic.width - 5
        y = 5
        image.paste(current_graphic, (x, y))

    # Rotation/Inversion
    if ROTATED:
        image = image.rotate(180)
    if INVERTED:
        image = ImageOps.invert(image.convert("L")).convert("1")

    # Partial refresh
    epd.displayPartial(epd.getbuffer(image))

    # Save state
    with open(STATE_FILE, "w") as f:
        json.dump({
            "rotated": ROTATED,
            "inverted": INVERTED,
            "graphic": f"pik{GRAPHIC_INDEX}"
        }, f)

    time.sleep(INTERVAL)