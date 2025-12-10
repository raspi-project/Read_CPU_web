# monitor.py
import threading
import time
import os
import psutil
from PIL import Image, ImageDraw, ImageFont
import board
import adafruit_ssd1306
import RPi.GPIO as GPIO

# -------------------------
# CONFIG
# -------------------------
FAN_PIN = 26
TEMP_SAFE_THRESHOLD = 55.0
OLED_WIDTH = 128
OLED_HEIGHT = 64
I2C_ADDR = 0x3C
POLL_INTERVAL = 1.0

state = {
    "cpu_percent": 0.0,
    "cpu_temp": None,
    "ram_used_mb": 0,
    "ram_total_mb": 0,
    "ram_percent": 0,
    "disk_used_gb": 0,
    "disk_total_gb": 0,
    "disk_percent": 0,
    "fan_actual_on": False,
    "fan_manual_state": False,
    "fan_forced_auto": False
}
state_lock = threading.Lock()

# -------------------------
# Temp Reader
# -------------------------
def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read().strip()) / 1000.0
    except:
        return None

# -------------------------
# GPIO Setup
# -------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.output(FAN_PIN, GPIO.LOW)

# -------------------------
# OLED Setup
# -------------------------
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=I2C_ADDR)
oled.fill(0)
oled.show()
font = ImageFont.load_default()

# -------------------------
# Monitor Loop
# -------------------------
def monitor_loop():
    while True:
        cpu = psutil.cpu_percent(interval=None)
        cpu_temp = get_cpu_temp()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        ram_used_mb = ram.used // (1024**2)
        ram_total_mb = ram.total // (1024**2)
        disk_used_gb = disk.used // (1024**3)
        disk_total_gb = disk.total // (1024**3)

        forced = cpu_temp and cpu_temp > TEMP_SAFE_THRESHOLD
        with state_lock:
            state["cpu_percent"] = cpu
            state["cpu_temp"] = cpu_temp
            state["ram_used_mb"] = ram_used_mb
            state["ram_total_mb"] = ram_total_mb
            state["ram_percent"] = ram.percent
            state["disk_used_gb"] = disk_used_gb
            state["disk_total_gb"] = disk_total_gb
            state["disk_percent"] = disk.percent
            state["fan_forced_auto"] = forced

            # Determine actual fan state
            if forced:
                actual_on = True
            else:
                actual_on = state["fan_manual_state"]

            state["fan_actual_on"] = actual_on

        GPIO.output(FAN_PIN, GPIO.HIGH if state["fan_actual_on"] else GPIO.LOW)

        # ---------------- OLED ----------------
        try:
            image = Image.new("1", (OLED_WIDTH, OLED_HEIGHT))
            draw = ImageDraw.Draw(image)

            draw.text((0, 0), f"CPU: {cpu}%", font=font, fill=255)
            draw.text((0, 12), f"Temp: {cpu_temp:.1f}C" if cpu_temp else "Temp: NA", font=font, fill=255)
            draw.text((0, 24), f"RAM: {ram_used_mb}/{ram_total_mb}MB", font=font, fill=255)
            draw.text((0, 36), f"Disk: {disk_used_gb}/{disk_total_gb}GB", font=font, fill=255)

            if state["fan_actual_on"]:
                txt = "FAN ON (AUTO)" if forced else "FAN ON"
            else:
                txt = "FAN OFF"
            draw.text((0, 48), txt, font=font, fill=255)

            oled.image(image)
            oled.show()

        except Exception as e:
            print("OLED ERROR:", e)

        # -------- Terminal Output --------
        os.system("clear")
        print("====== RASPBERRY PI SYSTEM MONITOR ======")
        print(f"CPU: {cpu}%")
        print(f"TEMP: {cpu_temp}°C")
        print(f"RAM: {ram.percent}% ({ram_used_mb}/{ram_total_mb}MB)")
        print(f"DISK: {disk.percent}% ({disk_used_gb}/{disk_total_gb}GB)")
        print(f"FAN: {'ON' if state['fan_actual_on'] else 'OFF'}")
        print("=========================================")

        time.sleep(POLL_INTERVAL)

def start_monitor():
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()
