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

# ---------------- PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "lib"))
sys.path.append(LIB_DIR)

from waveshare_epd import epd2in13_V4

# ---------------- CONFIG ----------------
DISK_PATH = "/"
CONTROL_FILE = "control.json"
STATE_FILE = "state.json"
XP_FILE = "xp.json"

GRAPHIC_PREFIX = "pik"
GRAPHIC_COUNT = 10
INTERVAL = 7

# ---------------- PHRASES ----------------
PHRASES = [
    ("Sire! Log in via thy browser!", "Thy IP and port 8080"),
    ("Sire! Thy IP and THY port!", "They shall show the way!"),
    ("Sire! IP:8080 login My liege!", "Command thy legion!"),
    ("Sire, Thy share \\\\IP\\private", "I shall keep thy data safe!"),
    ("I am PiTemplar sire!", "Data Bank is my sacred duty!"),
    ("Guard thy bits, my liege!", "The vault stands ready!"),
    ("Thy server awakens!", "8080 awaits thy command!"),
    ("Sire! V1.2.2 stands firm!", "No packets shall falter!"),
    ("I watch thy disks, sire!", "Not a byte goes astray!"),
    ("Rest easy, my liege!", "PiTemplar Version 1.2.2")
]

# ---------------- STATE ----------------
ROTATED = False
INVERTED = False
GRAPHIC_INDEX = 8
LAST_DISK_USED = 0

# ---------------- XP SYSTEM ----------------
def read_xp():
    try:
        with open(XP_FILE, "r") as f:
            data = json.load(f)

        if not all(k in data for k in ("level", "xp", "xp_to_next")):
            raise ValueError

        if data["xp_to_next"] <= 0:
            data["xp_to_next"] = 10

        return data
    except:
        return {"level": 1, "xp": 0, "xp_to_next": 10}


def write_xp(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f)


def add_xp(amount=2):
    data = read_xp()
    data["xp"] += amount

    leveled_up = False

    while data["xp"] >= data["xp_to_next"]:
        data["xp"] -= data["xp_to_next"]
        data["level"] += 1

        if data["xp_to_next"] < 10000:
            data["xp_to_next"] *= 2

        leveled_up = True

    write_xp(data)
    return data, leveled_up

# ---------------- SYSTEM ----------------
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
    return int((d.used / d.total) * 100)


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

# ---------------- DISK XP ----------------
def check_disk_activity():
    global LAST_DISK_USED
    current = get_disk_usage(DISK_PATH)

    if abs(current - LAST_DISK_USED) >= 1:
        LAST_DISK_USED = current
        add_xp()

# ---------------- BOOT FLIP ----------------
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

font = ImageFont.load_default()
try:
    title_font = ImageFont.truetype("fonts/PirataOne-Regular.ttf", 22)
except:
    title_font = font

graphics = []
for i in range(GRAPHIC_COUNT):
    filename = f"{GRAPHIC_PREFIX}{i}.png"
    graphics.append(
        Image.open(filename).convert("1") if os.path.exists(filename) else None
    )

print("⚔️ PiTemplar Final Build Active")

# ---------------- MAIN LOOP ----------------
while True:
    control = read_control()
    force_update = False
    level_up_message = None

    if control.get("flip"):
        ROTATED = not ROTATED
        control["flip"] = False
        force_update = True
        xp_data, leveled = add_xp()
        if leveled:
            level_up_message = xp_data

    if control.get("invert"):
        INVERTED = not INVERTED
        control["invert"] = False
        force_update = True
        xp_data, leveled = add_xp()
        if leveled:
            level_up_message = xp_data

    if control.get("refresh"):
        control["refresh"] = False
        force_update = True
        xp_data, leveled = add_xp()
        if leveled:
            level_up_message = xp_data

    if force_update:
        write_control(control)

    check_disk_activity()

    GRAPHIC_INDEX = (GRAPHIC_INDEX + 1) % GRAPHIC_COUNT

    used_percent = get_disk_usage(DISK_PATH)
    ssid = get_ssid()
    ip_addr = get_ip("wlan0")
    cpu_temp = get_cpu_temp()

    xp_data = read_xp()
    level = xp_data["level"]
    xp = xp_data["xp"]
    xp_to_next = xp_data["xp_to_next"]

    # -------- IMAGE --------
    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    # -------- TITLE + LEVEL --------
    title_text = "PiTemplar"
    draw.text((5, 5), title_text, font=title_font, fill=0)
    title_width = draw.textlength(title_text, font=title_font)

    level_text = f"Lv:{level}"
    level_x = 5 + title_width + 5
    draw.text((level_x, 10), level_text, font=font, fill=0)

    # -------- XP BAR (under Lv) --------
    bar_x = int(level_x)
    bar_y = 22
    bar_width = 50
    bar_height = 5

    progress = int((xp / xp_to_next) * bar_width)

    draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), outline=0)
    draw.rectangle((bar_x, bar_y, bar_x + progress, bar_y + bar_height), fill=0)

    # -------- DIVIDER --------
    draw.line((5, 30, epd.height - 5, 30), fill=0)

    # -------- PHRASES --------
    if level_up_message:
        line1 = "Sire! I have grown stronger!"
        line2 = f"Level {level_up_message['level']} attained!"
    else:
        line1, line2 = PHRASES[GRAPHIC_INDEX]

    draw.text((5, 35), line1, font=font, fill=0)
    draw.text((5, 48), line2, font=font, fill=0)

    # -------- SYSTEM INFO --------
    draw.text((5, 75), f"Disk Used: {used_percent}%", font=font, fill=0)
    draw.text((5, 90), f"WiFi: {ssid}", font=font, fill=0)

    # -------- CPU --------
    draw.text((5, 118), f"CPU: {cpu_temp}", font=font, fill=0)

    # -------- GRAPHIC --------
    current_graphic = graphics[GRAPHIC_INDEX]
    if current_graphic:
        x = epd.height - current_graphic.width - 5
        image.paste(current_graphic, (x, 5))

    # -------- IP (DRAW LAST - ALWAYS FULL) --------
    ip_text = f"IP: {ip_addr}"
    draw.text((5, 105), ip_text, font=font, fill=0)

    # -------- ROTATE / INVERT --------
    if ROTATED:
        image = image.rotate(180)
    if INVERTED:
        image = ImageOps.invert(image.convert("L")).convert("1")

    epd.displayPartial(epd.getbuffer(image))

    with open(STATE_FILE, "w") as f:
        json.dump({
            "level": level,
            "xp": xp
        }, f)

    time.sleep(INTERVAL)