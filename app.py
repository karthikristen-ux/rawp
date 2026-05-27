"""
Radioactive Water Predictor — Flask Backend
=============================================
REST API server that receives TDS data from ESP32 hardware,
runs the prediction engine, serves the dashboard, and manages alerts.

Endpoints:
    GET  /              → Serve dashboard
    POST /api/sensor    → Receive TDS from ESP32
    GET  /api/readings  → All historical readings
    GET  /api/latest    → Latest reading + full analysis
    POST /api/analyze   → Manual analysis with custom TDS
    POST /api/alert     → Send NGO alert for latest reading
    GET  /api/status    → ESP32 connection status
    GET  /api/alerts    → Alert history
"""

import os
import time
import json
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

from config import SERVER_HOST, SERVER_PORT, DEBUG_MODE, SENSOR_TIMEOUT_SECONDS
from prediction_engine import full_analysis
from alert_system import send_alert, get_alert_history

# ─── Flask App Setup ───
app = Flask(__name__)
CORS(app)

# ─── In-Memory State ───
latest_reading = None
last_sensor_time = 0
readings_history = []
esp_location = "ESP32 Sensor"  # Default location for ESP32 readings
is_monitoring_active = False   # Toggle to ignore ESP32 data manually
CSV_FILE = "water_data.csv"

# Load existing data
if os.path.exists(CSV_FILE):
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"[INFO] Loaded {len(df)} historical readings from {CSV_FILE}")
    except Exception:
        df = pd.DataFrame()


# ═══════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def dashboard():
    """Serve the main dashboard page."""
    return render_template("index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files (CSS, JS)."""
    return send_from_directory("static", filename)


# ─── ESP32 SENSOR DATA INGESTION ───

@app.route("/api/sensor", methods=["POST"])
def receive_sensor_data():
    """
    Receive TDS reading from ESP32 via HTTP POST.
    Uses the location set from dashboard (via /api/set-location).
    """
    global latest_reading, last_sensor_time
    
    # Update last_sensor_time so the dashboard knows the ESP32 is still connected and alive
    last_sensor_time = time.time()
    
    # If monitoring is manually stopped from the dashboard, ignore incoming data safely
    if not is_monitoring_active:
        return jsonify({"status": "ignored", "message": "Monitoring is currently paused"}), 200
        
    try:
        # Accept both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        tds = float(data.get("tds", 0))
        # Use the dashboard-set location, falling back to ESP32's value
        location = esp_location or data.get("location", "ESP32 Sensor")
        
        # If TDS is extremely low (sensor out of water picking up noise),
        # we skip analysis and CSV logging, but the dashboard still knows it's connected
        if tds <= 10.0:
            return jsonify({"status": "ignored", "message": "Sensor out of water, data skipped"}), 200
        
        
        # Run full analysis
        analysis = full_analysis(tds, location)
        analysis["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update state
        latest_reading = analysis
        last_sensor_time = time.time()
        readings_history.append(analysis)
        
        # Keep only last 500 readings in memory
        if len(readings_history) > 500:
            readings_history.pop(0)
        
        # Save to CSV
        _save_to_csv(analysis)
        
        print(f"[SENSOR] TDS={tds} | Risk={analysis['risk_score']}% | Element={analysis['radioactive_element']['element']}")
        
        return jsonify({
            "status": "ok",
            "risk_score": analysis["risk_score"],
            "element": analysis["radioactive_element"]["element"],
        }), 200
    
    except Exception as e:
        print(f"[ERROR] Sensor data error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


# ─── LATEST READING ───

@app.route("/api/latest", methods=["GET"])
def get_latest():
    """Return the latest reading with full analysis."""
    if latest_reading is None:
        return jsonify({"status": "no_data", "message": "No sensor data received yet."}), 200
    
    return jsonify({
        "status": "ok",
        "data": latest_reading,
        "esp32_connected": _is_esp32_connected(),
    }), 200


# ─── ALL READINGS ───

@app.route("/api/readings", methods=["GET"])
def get_readings():
    """Return all readings history."""
    limit = request.args.get("limit", 50, type=int)
    readings = readings_history[-limit:]
    return jsonify({
        "status": "ok",
        "count": len(readings),
        "data": readings,
    }), 200


# ─── MANUAL ANALYSIS ───

@app.route("/api/set-location", methods=["POST"])
def set_esp_location():
    """Set the location name for ESP32 sensor readings from the dashboard."""
    global esp_location, is_monitoring_active
    data = request.get_json()
    esp_location = data.get("location", "ESP32 Sensor")
    is_monitoring_active = True  # Automatically start monitoring when location is set
    return jsonify({"status": "ok", "location": esp_location}), 200


@app.route("/api/toggle-monitoring", methods=["POST"])
def toggle_monitoring():
    """Start or stop accepting data from the ESP32."""
    global is_monitoring_active
    data = request.get_json()
    is_monitoring_active = data.get("active", False)
    status = "started" if is_monitoring_active else "stopped"
    print(f"[INFO] Monitoring manually {status}")
    return jsonify({"status": "ok", "is_active": is_monitoring_active}), 200


@app.route("/api/analyze", methods=["POST"])
def manual_analyze():
    """
    Run analysis with manually entered values.
    Supports optional overrides for pH, hardness, nitrate, sulfate.
    If not provided, these are auto-derived from TDS.
    
    Expected JSON: {"tds": 750, "location": "Manual Test", "ph": 7.5, ...}
    """
    global latest_reading, last_sensor_time
    
    try:
        data = request.get_json()
        tds = float(data.get("tds", 0))
        location = data.get("location", "Manual Input")
        
        analysis = full_analysis(tds, location)
        
        # Apply manual overrides if provided
        overrides = {}
        for key in ['ph', 'hardness', 'nitrate', 'sulfate']:
            if key in data and data[key] is not None:
                val = float(data[key])
                analysis['parameters'][key] = val
                overrides[key] = val
        
        # Recalculate risk score and comparison if overrides were applied
        if overrides:
            from prediction_engine import calculate_risk_score, get_risk_level, get_comparison
            analysis['risk_score'] = calculate_risk_score(analysis['parameters'])
            analysis['risk_level'] = get_risk_level(analysis['risk_score'])
            analysis['comparison'] = get_comparison(analysis['parameters'])
        
        analysis["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        latest_reading = analysis
        last_sensor_time = time.time()
        readings_history.append(analysis)
        
        _save_to_csv(analysis)
        
        return jsonify({
            "status": "ok",
            "data": analysis,
        }), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# ─── NGO ALERT ───

@app.route("/api/alert", methods=["POST"])
def trigger_alert():
    """Send the latest water quality report to NGOs. Accepts optional custom email."""
    if latest_reading is None:
        return jsonify({"status": "error", "message": "No data to send. Run an analysis first."}), 400
    
    # Accept custom email from request body
    custom_email = None
    if request.is_json:
        data = request.get_json()
        custom_email = data.get("email", "").strip() if data else None
    
    result = send_alert(latest_reading, custom_email=custom_email)
    return jsonify(result), 200


# ─── ALERT HISTORY ───

@app.route("/api/alerts", methods=["GET"])
def alert_history():
    """Return history of sent alerts."""
    return jsonify({
        "status": "ok",
        "alerts": get_alert_history(),
    }), 200


# ─── ESP32 STATUS ───

@app.route("/api/status", methods=["GET"])
def esp32_status():
    """Check if ESP32 is connected (received data recently)."""
    connected = _is_esp32_connected()
    elapsed = int(time.time() - last_sensor_time) if last_sensor_time > 0 else -1
    
    return jsonify({
        "connected": connected,
        "last_seen_seconds_ago": elapsed,
        "total_readings": len(readings_history),
    }), 200


# ─── CSV DOWNLOAD ───

@app.route("/api/download", methods=["GET"])
def download_csv():
    """Download the water_data.csv file."""
    if os.path.exists(CSV_FILE):
        return send_from_directory(
            os.path.dirname(os.path.abspath(CSV_FILE)) or ".",
            os.path.basename(CSV_FILE),
            as_attachment=True,
            download_name="water_report.csv",
            mimetype="text/csv"
        )
    return jsonify({"status": "error", "message": "No data file found."}), 404


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def _is_esp32_connected() -> bool:
    """Check if ESP32 has sent data recently."""
    if last_sensor_time == 0:
        return False
    return (time.time() - last_sensor_time) < SENSOR_TIMEOUT_SECONDS


def _save_to_csv(analysis: dict):
    """Append analysis result to CSV file."""
    try:
        params = analysis["parameters"]
        row = {
            "Timestamp": analysis["timestamp"],
            "Location": analysis["location"],
            "TDS": params["tds"],
            "pH": params["ph"],
            "Hardness": params["hardness"],
            "Nitrate": params["nitrate"],
            "Sulfate": params["sulfate"],
            "Chloride": params["chloride"],
            "Conductivity": params["conductivity"],
            "Turbidity": params["turbidity"],
            "RiskScore": analysis["risk_score"],
            "Element": analysis["radioactive_element"]["element"],
            "Isotope": analysis["radioactive_element"]["isotope"],
        }
        
        new_df = pd.DataFrame([row])
        
        if os.path.exists(CSV_FILE):
            old_df = pd.read_csv(CSV_FILE)
            combined = pd.concat([old_df, new_df], ignore_index=True)
        else:
            combined = new_df
        
        combined.to_csv(CSV_FILE, index=False)
    except Exception as e:
        print(f"[WARNING] Could not save to CSV: {e}")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import socket
    
    # Get local IP for display
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"
    
    print("=" * 60)
    print("  [*] RADIOACTIVE WATER PREDICTOR - SERVER")
    print("=" * 60)
    print(f"  Dashboard:  http://localhost:{SERVER_PORT}")
    print(f"  Network:    http://{local_ip}:{SERVER_PORT}")
    print(f"  ESP32 API:  http://{local_ip}:{SERVER_PORT}/api/sensor")
    print(f"")
    print(f"  Set this IP in your ESP32 Arduino code:")
    print(f"    const char* serverIP = \"{local_ip}\";")
    print("=" * 60)
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
