# app.py
from flask import Flask, jsonify, render_template
import threading
import time
import RPi.GPIO as GPIO
from monitor import get_all_stats

GPIO.setmode(GPIO.BCM)
FAN_PIN = 17
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.output(FAN_PIN, GPIO.LOW)

app = Flask(__name__, template_folder='.')

fan_state = False  # false = off , true = on

def auto_fan_control():
    global fan_state
    while True:
        stats = get_all_stats()
        temp = stats["temperature"]

        if temp > 55:
            GPIO.output(FAN_PIN, GPIO.HIGH)
            fan_state = True
        else:
            GPIO.output(FAN_PIN, GPIO.LOW)
            fan_state = False

        time.sleep(2)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    stats = get_all_stats()
    stats["fan_state"] = fan_state
    return jsonify(stats)

@app.route("/fan/on")
def fan_on():
    global fan_state
    GPIO.output(FAN_PIN, GPIO.HIGH)
    fan_state = True
    return jsonify({"fan": "ON"})

@app.route("/fan/off")
def fan_off():
    global fan_state
    GPIO.output(FAN_PIN, GPIO.LOW)
    fan_state = False
    return jsonify({"fan": "OFF"})

if __name__ == "__main__":
    threading.Thread(target=auto_fan_control, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
