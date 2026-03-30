"""
iot_simulator/sensor_simulator.py
─────────────────────────────────────────────────────────────────────────────
Smart Solar Optimization – IoT Sensor Simulator
Simulates data from Temperature, Light (LDR/BH1750), and Dust sensors.
In production replace this with actual Arduino/Raspberry Pi serial reads.

Sends sensor data to the backend REST API every N seconds.
─────────────────────────────────────────────────────────────────────────────

ACTUAL ARDUINO SENSOR SKETCH (paste this into Arduino IDE):
──────────────────────────────────────────────────────────
#include <Wire.h>
#include <BH1750.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT22
#define DUST_PIN A0
#define VOLTAGE_PIN A1

DHT dht(DHTPIN, DHTTYPE);
BH1750 lightMeter;

void setup() {
  Serial.begin(9600);
  Wire.begin();
  dht.begin();
  lightMeter.begin();
}

void loop() {
  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();
  float lux = lightMeter.readLightLevel();
  int dustRaw = analogRead(DUST_PIN);
  float dustDensity = (0.17 * (dustRaw * (5.0 / 1023.0)) - 0.1) * 100;
  float voltage = analogRead(VOLTAGE_PIN) * (5.0 / 1023.0) * 5;  // voltage divider

  Serial.print("{");
  Serial.print("\"temp\":"); Serial.print(temp); Serial.print(",");
  Serial.print("\"light\":"); Serial.print(lux); Serial.print(",");
  Serial.print("\"dust\":"); Serial.print(dustDensity); Serial.print(",");
  Serial.print("\"voltage\":"); Serial.print(voltage);
  Serial.println("}");
  delay(5000);
}
──────────────────────────────────────────────────────────
"""

import time
import math
import random
import json
import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Try to import serial for real hardware (optional)
try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


API_BASE_URL = "http://localhost:5000"


# ─────────────────────────────────────────────
#  Simulated Sensor Readings
# ─────────────────────────────────────────────

def simulate_temperature() -> float:
    """DHT22 temperature simulation (°C)."""
    hour = datetime.datetime.now().hour
    base_temp = 25 + 15 * max(0, math.sin(math.pi * (hour - 6) / 12))
    return round(base_temp + random.gauss(0, 1.5), 1)


def simulate_light_intensity() -> float:
    """BH1750 light sensor (lux / W/m²)."""
    hour = datetime.datetime.now().hour
    peak = max(0, math.sin(math.pi * (hour - 6) / 12))
    return round(peak * 1000 + random.gauss(0, 40), 1)


def simulate_dust_level() -> float:
    """GP2Y1010AU0F dust sensor (µg/m³ → 0-100 scale)."""
    hour = datetime.datetime.now().hour
    # Dust accumulates during the day
    base = 5 + hour * 0.8
    return round(min(60, base + random.gauss(0, 3)), 1)


def simulate_voltage() -> float:
    """Voltage divider reading from panels (V)."""
    hour = datetime.datetime.now().hour
    sun = max(0, math.sin(math.pi * (hour - 6) / 12))
    return round(12 + sun * 12 + random.gauss(0, 0.5), 2)


def simulate_current() -> float:
    """ACS712 current sensor (A)."""
    hour = datetime.datetime.now().hour
    sun = max(0, math.sin(math.pi * (hour - 6) / 12))
    return round(sun * 6 + random.gauss(0, 0.2), 2)


def read_all_sensors(use_hardware: bool = False, port: str = "/dev/ttyUSB0") -> dict:
    """
    Collect all sensor readings.
    Set use_hardware=True and port to your Arduino's serial port
    when running on actual Raspberry Pi hardware.
    """
    if use_hardware and HAS_SERIAL:
        return _read_from_serial(port)
    return _read_simulated()


def _read_simulated() -> dict:
    temp    = simulate_temperature()
    light   = simulate_light_intensity()
    dust    = simulate_dust_level()
    voltage = simulate_voltage()
    current = simulate_current()
    return {
        "temperature"      : temp,
        "light_intensity"  : light,
        "dust_level"       : dust,
        "voltage"          : voltage,
        "current"          : current,
        "power_output"     : round(voltage * current / 1000, 3),   # kW
        "battery_percentage": min(100, int(50 + (voltage - 12) / 12 * 50)),
        "timestamp"        : datetime.datetime.now().isoformat(),
        "source"           : "simulator"
    }


def _read_from_serial(port: str, baud: int = 9600, timeout: int = 3) -> dict:
    """Read JSON line from Arduino over USB serial."""
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
        line = ser.readline().decode("utf-8").strip()
        ser.close()
        raw = json.loads(line)
        return {
            "temperature"      : raw.get("temp", 0),
            "light_intensity"  : raw.get("light", 0),
            "dust_level"       : raw.get("dust", 0),
            "voltage"          : raw.get("voltage", 0),
            "current"          : raw.get("current", 0),
            "power_output"     : round(raw.get("voltage", 0) * raw.get("current", 0) / 1000, 3),
            "battery_percentage": 50,
            "timestamp"        : datetime.datetime.now().isoformat(),
            "source"           : "hardware"
        }
    except Exception as e:
        print(f"⚠️  Serial read failed ({e}). Falling back to simulator.")
        return _read_simulated()


# ─────────────────────────────────────────────
#  Alert Logic
# ─────────────────────────────────────────────

def check_alerts(data: dict) -> list:
    alerts = []
    if data["dust_level"] > 20:
        alerts.append({"level": "WARNING", "message": "High dust – cleaning needed"})
    if data["temperature"] > 50:
        alerts.append({"level": "DANGER",  "message": "Panel overheating!"})
    if data["battery_percentage"] < 20:
        alerts.append({"level": "DANGER",  "message": "Battery critically low"})
    if data["power_output"] < 0.5 and 9 <= datetime.datetime.now().hour <= 15:
        alerts.append({"level": "WARNING", "message": "Low output during peak hours"})
    return alerts


# ─────────────────────────────────────────────
#  Main Loop
# ─────────────────────────────────────────────

def run(interval_seconds: int = 5, use_hardware: bool = False, arduino_port: str = "/dev/ttyUSB0"):
    print(f"🌞 Smart Solar IoT Simulator started (interval={interval_seconds}s)")
    print(f"   Hardware mode: {'ON - ' + arduino_port if use_hardware else 'OFF (simulated)'}")
    print("   Press Ctrl+C to stop.\n")

    while True:
        data = read_all_sensors(use_hardware=use_hardware, port=arduino_port)
        alerts = check_alerts(data)

        print(f"[{data['timestamp']}]")
        print(f"  🌡  Temp      : {data['temperature']} °C")
        print(f"  💡  Light     : {data['light_intensity']} W/m²")
        print(f"  🌫  Dust      : {data['dust_level']}")
        print(f"  ⚡  Power     : {data['power_output']} kW")
        print(f"  🔋  Battery   : {data['battery_percentage']} %")
        if alerts:
            for a in alerts:
                print(f"  ⚠️  [{a['level']}] {a['message']}")
        print()

        # POST to backend API if available
        if HAS_REQUESTS:
            try:
                resp = requests.post(f"{API_BASE_URL}/api/sensor-data", json=data, timeout=2)
                if resp.status_code != 200:
                    print(f"  API warn: {resp.status_code}")
            except Exception:
                pass   # API not running – still log locally

        time.sleep(interval_seconds)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Smart Solar IoT Simulator")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval (seconds)")
    parser.add_argument("--hardware", action="store_true", help="Use real Arduino via serial")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Arduino serial port")
    args = parser.parse_args()

    run(interval_seconds=args.interval, use_hardware=args.hardware, arduino_port=args.port)
