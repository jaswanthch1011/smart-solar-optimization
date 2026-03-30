# 🌞 Smart Solar Optimization System
**Team Fantastic Four 😎 | Hackxtreme – GDG × GLEC**
> Jaswanth CH · Naga Teja J · Radhakrishna CH · Sindhuri Reddy E
> Gokaraju Lailavathi Engineering College

---

## 📋 Project Overview

An AI + IoT-powered system that:
- **Optimizes solar panel placement** using astronomical calculations
- **Predicts power output** using a Machine Learning model (RandomForest)
- **Monitors sensors in real-time** (temperature, light, dust, voltage, current)
- **Generates predictive maintenance alerts** before failures happen
- **Shows government solar schemes** to improve awareness
- **Provides a web dashboard** for all customer segments

---

## 🗂️ Project Structure

```
smart-solar/
├── backend/
│   ├── app.py              ← Flask REST API (all endpoints)
│   └── requirements.txt    ← Python dependencies
├── frontend/
│   └── index.html          ← Full web dashboard (no build step needed)
├── ml_model/
│   └── solar_predictor.py  ← ML training + prediction module
├── iot_simulator/
│   └── sensor_simulator.py ← IoT simulator + Arduino integration
└── README.md
```

---

## 🚀 Quick Start

### 1. Backend (Flask API)
```bash
cd backend
pip install -r requirements.txt
python app.py
# → Running on http://localhost:5000
```

### 2. Frontend (Web Dashboard)
```bash
# Just open the file in a browser — no build step needed!
open frontend/index.html
# Or serve with Python:
cd frontend && python -m http.server 8080
# → http://localhost:8080
```

### 3. ML Model (train + test)
```bash
cd ml_model
pip install scikit-learn numpy
python solar_predictor.py
# Trains model, saves solar_model.pkl, prints sample predictions
```

### 4. IoT Simulator
```bash
cd iot_simulator
pip install requests
python sensor_simulator.py --interval 5
# With real Arduino:
python sensor_simulator.py --hardware --port /dev/ttyUSB0
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/sensor-data`       | Live sensor readings |
| GET  | `/api/alerts`            | Maintenance alerts |
| POST | `/api/optimize-placement`| Optimal tilt & orientation |
| POST | `/api/predict-output`    | ML-based power prediction |
| GET  | `/api/energy-history`    | 7-day energy chart data |
| GET  | `/api/government-schemes`| Solar subsidy schemes |
| POST | `/api/customer-support`  | Support chat response |

### Example: Optimize Placement
```bash
curl -X POST http://localhost:5000/api/optimize-placement \
  -H "Content-Type: application/json" \
  -d '{"latitude": 17.38, "longitude": 78.48, "month": 6}'
```

### Example: Predict Output
```bash
curl -X POST http://localhost:5000/api/predict-output \
  -H "Content-Type: application/json" \
  -d '{"temperature": 38, "dust_level": 15, "tilt_angle": 20, "panel_capacity_kw": 5}'
```

---

## 🛠️ Technologies Used

| Layer | Technology |
|-------|-----------|
| ML / AI | Python, scikit-learn (RandomForest), NumPy |
| Backend | Python, Flask, REST APIs |
| Frontend | HTML5, CSS3, JavaScript, Chart.js |
| IoT | Arduino (DHT22, BH1750, GP2Y1010AU0F), Raspberry Pi |
| Cloud (prod) | Firebase / AWS / Google Cloud |
| Version Control | Git & GitHub |

---

## 📡 Hardware Setup (Arduino)

**Sensors:**
- **DHT22** → Temperature & Humidity (pin D4)
- **BH1750** → Light intensity via I2C
- **GP2Y1010AU0F** → Dust density (analog pin A0)
- **Voltage Divider** → Panel voltage (analog pin A1)
- **ACS712** → Current sensor

Upload the Arduino sketch from `iot_simulator/sensor_simulator.py` (top of file) to your Arduino, then run:
```bash
python iot_simulator/sensor_simulator.py --hardware --port /dev/ttyUSB0
```

---

## 🌐 Customer Segments

- **Residential Users** – Monitor home rooftop solar
- **Commercial / Industrial** – Track large-scale installations
- **Maintenance Teams** – Get fault alerts and cleaning schedules
- **Government / Smart Cities** – Aggregate data across installations

---

## 📈 Key Features

✅ Real-time sensor dashboard (auto-refreshes every 5s)  
✅ Physics + ML based power output prediction  
✅ Astronomically-accurate panel placement optimizer  
✅ Predictive maintenance alerts (dust, temperature, battery)  
✅ 7-day energy history chart  
✅ Government scheme awareness section  
✅ Customer support chat  
✅ Works offline (frontend has local fallback calculations)  

---

## 🏆 Hackxtreme – GDG × GLEC
*Sustainable energy through intelligent systems.*
