# app.py
from flask import Flask, jsonify, request, render_template
from monitor import start_monitor, state, state_lock, TEMP_SAFE_THRESHOLD
import RPi.GPIO as GPIO

app = Flask(__name__)

# Start background thread
start_monitor()

@app.route("/")
def index():
    return render_template("index.html", threshold=TEMP_SAFE_THRESHOLD)

@app.route("/status")
def status():
    with state_lock:
        return jsonify(state)

@app.route("/set_fan", methods=["POST"])
def set_fan():
    data = request.json
    manual = bool(data["manual_state"])

    with state_lock:
        state["fan_manual_state"] = manual

        # Only apply immediately if not in AUTO mode
        if not state["fan_forced_auto"]:
            state["fan_actual_on"] = manual
            GPIO.output(26, GPIO.HIGH if manual else GPIO.LOW)

    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
