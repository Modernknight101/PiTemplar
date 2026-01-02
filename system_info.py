import shutil
import socket
import fcntl
import struct

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
            return f"{int(f.read())/1000:.1f}°C"
    except:
        return "N/A"

def get_disk_usage(path="/"):
    d = shutil.disk_usage(path)
    return {
        "total_gb": round(d.total / 1024**3, 1),
        "used_gb": round(d.used / 1024**3, 1),
        "free_gb": round(d.free / 1024**3, 1),
        "used_percent": int(d.used / d.total * 100),
    }
