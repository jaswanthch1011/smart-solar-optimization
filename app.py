from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import math
import datetime
import json
from solar_predictor import predict_output, load_model
from flask import Flask, jsonify, request
from solar_predictor import predict_output, load_model
model = load_model()
model = load_model()


app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
#  Mock sensor data store (replace with Firebase / AWS in prod)
# ─────────────────────────────────────────────
sensor_store = {
    "temperature": 35.2,
    "light_intensity": 850,
    "dust_level": 12,
    "power_output": 4.7,
    "battery_percentage": 78,
    "voltage": 24.3,
    "current": 5.1,
    "panel_angle": 30,
    "panel_orientation": "South",
}

government_schemes = [
    {
        "name": "PM Surya Ghar Muft Bijli Yojana",
        "benefit": "Free electricity up to 300 units/month for rooftop solar",
        "subsidy": "Up to ₹78,000 subsidy",
        "link": "https://pmsuryaghar.gov.in"
    },
    {
        "name": "Telangana Solar Policy 2015",
        "benefit": "Net metering + wheeling for surplus energy",
        "subsidy": "State-level incentives for solar installations",
        "link": "https://tgredco.gov.in"
    },
    {
        "name": "MNRE Rooftop Solar Scheme",
        "benefit": "40% subsidy for up to 2 kW, 20% for 2–3 kW",
        "subsidy": "Central Financial Assistance (CFA)",
        "link": "https://mnre.gov.in"
    },
]

# ─────────────────────────────────────────────
#  Helper: simulate fluctuating sensor values
# ─────────────────────────────────────────────
def get_live_sensor_data():
    hour = datetime.datetime.now().hour
    sun_factor = max(0, math.sin(math.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0
    return {
        "temperature": round(25 + sun_factor * 20 + random.uniform(-2, 2), 1),
        "light_intensity": round(sun_factor * 1000 + random.uniform(-50, 50)),
        "dust_level": round(random.uniform(5, 30), 1),
        "power_output": round(sun_factor * 5 + random.uniform(-0.3, 0.3), 2),
        "battery_percentage": round(50 + sun_factor * 40 + random.uniform(-5, 5)),
        "voltage": round(22 + sun_factor * 4 + random.uniform(-0.5, 0.5), 1),
        "current": round(sun_factor * 6 + random.uniform(-0.2, 0.2), 2),
        "panel_angle": sensor_store["panel_angle"],
        "panel_orientation": sensor_store["panel_orientation"],
        "timestamp": datetime.datetime.now().isoformat()
    }

# ─────────────────────────────────────────────
#  Helper: simple rule-based maintenance alerts
# ─────────────────────────────────────────────
def generate_alerts(data):
    alerts = []
    if data["dust_level"] > 20:
        alerts.append({"type": "warning", "message": "High dust level detected. Cleaning recommended.", "icon": "🧹"})
    if data["temperature"] > 50:
        alerts.append({"type": "danger", "message": "Panel overheating! Check ventilation.", "icon": "🌡️"})
    if data["battery_percentage"] < 20:
        alerts.append({"type": "danger", "message": "Battery critically low.", "icon": "🔋"})
    if data["power_output"] < 1 and 8 <= datetime.datetime.now().hour <= 16:
        alerts.append({"type": "warning", "message": "Low power output during peak hours. Inspect panel.", "icon": "⚡"})
    if not alerts:
        alerts.append({"type": "success", "message": "All systems operating normally.", "icon": "✅"})
    return alerts

# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({"message": "Smart Solar Optimization API is running 🌞"})

latest_sensor_data = {}

@app.route("/api/sensor-data", methods=["GET", "POST"])
def sensor_data():
    global latest_sensor_data

    if request.method == "POST":
        latest_sensor_data = request.get_json()
        return jsonify({"status": "received"})

    return jsonify(latest_sensor_data if latest_sensor_data else get_live_sensor_data())

@app.route("/api/alerts", methods=["GET"])
def alerts():
    data = get_live_sensor_data()
    return jsonify(generate_alerts(data))

@app.route("/api/optimize-placement", methods=["POST"])
def optimize_placement():
    body = request.get_json(force=True)
    latitude = float(body.get("latitude", 17.38))   # default: Hyderabad
    longitude = float(body.get("longitude", 78.48))
    month = int(body.get("month", datetime.datetime.now().month))

    # Solar declination angle (approximate)
    day_of_year = (month - 1) * 30 + 15
    declination = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
    optimal_tilt = round(abs(latitude - declination), 1)
    optimal_orientation = "South" if latitude >= 0 else "North"
    peak_sun_hours = round(5 + 2 * math.cos(math.radians(latitude)), 2)

    return jsonify({
        "optimal_tilt_angle": optimal_tilt,
        "optimal_orientation": optimal_orientation,
        "estimated_peak_sun_hours": peak_sun_hours,
        "latitude": latitude,
        "longitude": longitude,
        "month": month,
        "recommendation": (
            f"Set panel tilt to {optimal_tilt}° facing {optimal_orientation} "
            f"for ~{peak_sun_hours} peak sun hours/day."
        )
    })

@app.route("/api/predict-output", methods=["POST"])
def predict_output_api():
    body = request.get_json(force=True)

    result = predict_output(
        temperature=float(body.get("temperature", 35)),
        light_intensity=800,
        dust_level=float(body.get("dust_level", 10)),
        tilt_angle=float(body.get("tilt_angle", 30)),
        hour_of_day=12,
        cloud_cover=10,
        model=model
    )

    return jsonify(result)

@app.route("/api/energy-history", methods=["GET"])
def energy_history():
    """Simulated 7-day energy generation history."""
    history = []
    base = datetime.datetime.now()
    for i in range(7):
        day = base - datetime.timedelta(days=6 - i)
        history.append({
            "date": day.strftime("%Y-%m-%d"),
            "energy_kwh": round(random.uniform(15, 28), 2),
            "savings_inr": round(random.uniform(90, 170), 2)
        })
    return jsonify(history)

@app.route("/api/government-schemes", methods=["GET"])
def get_government_schemes():
    return jsonify(government_schemes)

@app.route("/api/customer-support", methods=["POST"])
def customer_support():
    body = request.get_json(force=True)
    issue = body.get("issue", "").lower()
    responses = {
        "dust": "We recommend cleaning panels every 2 weeks or when dust_level > 20. Use a soft cloth and water.",
        "low power": "Low power may be due to shading, dust, or incorrect angle. Run the optimizer.",
        "battery": "Ensure battery connections are tight. Check if inverter settings match battery type.",
        "temperature": "Ensure adequate airflow under panels. Avoid installation on flat non-ventilated roofs.",
    }
    reply = next((v for k, v in responses.items() if k in issue), "Our support team will contact you within 24 hours.")
    return jsonify({"response": reply, "ticket_id": f"TKT-{random.randint(10000, 99999)}"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
