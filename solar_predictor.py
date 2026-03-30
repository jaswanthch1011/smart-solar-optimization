"""
ml_model/solar_predictor.py
─────────────────────────────────────────────────────────────────────────────
Smart Solar Optimization – ML Prediction Module
Uses scikit-learn RandomForestRegressor to predict daily energy output (kWh).

Features used:
  - temperature (°C)
  - light_intensity (W/m²)
  - dust_level (0-100 scale)
  - tilt_angle (degrees)
  - hour_of_day (0-23)
  - cloud_cover (0-100 %)

Target: power_output (kW)
─────────────────────────────────────────────────────────────────────────────
"""

import numpy as np
import pickle
import os
import math
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline


# ─────────────────────────────────────────────
#  1. Synthetic Dataset Generator
# ─────────────────────────────────────────────

def generate_synthetic_data(n_samples: int = 5000, seed: int = 42) -> tuple:
    """
    Generate realistic synthetic solar panel sensor readings.
    Returns (X: np.ndarray, y: np.ndarray)
    """
    rng = np.random.default_rng(seed)

    temperature    = rng.uniform(15, 55, n_samples)          # °C
    light_intensity= rng.uniform(0, 1100, n_samples)         # W/m²
    dust_level     = rng.uniform(0, 60, n_samples)           # 0-60 scale
    tilt_angle     = rng.uniform(0, 90, n_samples)           # degrees
    hour_of_day    = rng.integers(0, 24, n_samples)          # 0-23
    cloud_cover    = rng.uniform(0, 100, n_samples)          # 0-100 %

    # Physics-informed target generation
    sun_elevation  = np.maximum(0, np.sin(np.pi * (hour_of_day - 6) / 12))
    tilt_factor    = np.cos(np.radians(np.abs(tilt_angle - 15)))
    tilt_factor    = np.clip(tilt_factor, 0, 1)
    temp_loss      = np.maximum(0, (temperature - 25) * 0.004)
    dust_loss      = dust_level * 0.005
    cloud_loss     = cloud_cover * 0.007
    solar_irr      = light_intensity / 1000 * (1 - cloud_loss / 100)

    power_output = (
        5.0                          # panel rated capacity (kW)
        * solar_irr
        * sun_elevation
        * tilt_factor
        * (1 - temp_loss - dust_loss)
        + rng.normal(0, 0.05, n_samples)   # sensor noise
    )
    power_output = np.clip(power_output, 0, 5.5)

    X = np.column_stack([
        temperature, light_intensity, dust_level,
        tilt_angle, hour_of_day, cloud_cover
    ])
    return X, power_output


# ─────────────────────────────────────────────
#  2. Model Training
# ─────────────────────────────────────────────

FEATURE_NAMES = [
    "temperature", "light_intensity", "dust_level",
    "tilt_angle", "hour_of_day", "cloud_cover"
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "solar_model.pkl")


def train_model(save: bool = True) -> Pipeline:
    print("🌞 Generating synthetic training data …")
    X, y = generate_synthetic_data(n_samples=8000)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=4,
            n_jobs=-1,
            random_state=42
        ))
    ])

    print("🤖 Training RandomForest model …")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)
    print(f"✅ MAE  : {mae:.4f} kW")
    print(f"✅ R²   : {r2:.4f}")

    if save:
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(pipeline, f)
        print(f"💾 Model saved to {MODEL_PATH}")

    return pipeline


def load_model() -> Pipeline:
    if not os.path.exists(MODEL_PATH):
        print("⚠️  No saved model found. Training a new one …")
        return train_model()
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


# ─────────────────────────────────────────────
#  3. Prediction API
# ─────────────────────────────────────────────

def predict_output(
    temperature: float,
    light_intensity: float,
    dust_level: float,
    tilt_angle: float,
    hour_of_day: int,
    cloud_cover: float,
    model: Pipeline = None
) -> dict:
    """
    Predict solar power output given sensor readings.

    Returns a dict with predicted kW, efficiency losses, and a recommendation.
    """
    if model is None:
        model = load_model()

    features = np.array([[
        temperature, light_intensity, dust_level,
        tilt_angle, hour_of_day, cloud_cover
    ]])
    predicted_kw = float(model.predict(features)[0])
    predicted_kw = max(0, round(predicted_kw, 3))

    # Compute individual loss estimates (for dashboard display)
    temp_loss_pct  = max(0, (temperature - 25) * 0.4)
    dust_loss_pct  = dust_level * 0.5
    cloud_loss_pct = cloud_cover * 0.7

    recommendation = "System operating optimally."
    if dust_level > 20:
        recommendation = "🧹 Clean panels to recover up to {:.1f}% efficiency.".format(dust_loss_pct)
    elif temperature > 45:
        recommendation = "🌡️ High temperature detected. Ensure proper airflow."
    elif cloud_cover > 70:
        recommendation = "☁️ Heavy cloud cover. Expected low output today."

    return {
        "predicted_output_kw": predicted_kw,
        "estimated_daily_kwh": round(predicted_kw * 6, 2),   # assume ~6 peak hours
        "losses": {
            "temperature_loss_pct": round(temp_loss_pct, 1),
            "dust_loss_pct"       : round(dust_loss_pct, 1),
            "cloud_loss_pct"      : round(cloud_loss_pct, 1),
        },
        "recommendation": recommendation
    }


# ─────────────────────────────────────────────
#  4. Placement Optimizer
# ─────────────────────────────────────────────

def optimize_placement(latitude: float, month: int = None) -> dict:
    """
    Calculate optimal tilt angle and orientation for a given latitude and month.
    """
    if month is None:
        import datetime
        month = datetime.datetime.now().month

    day_of_year   = (month - 1) * 30 + 15
    declination   = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
    optimal_tilt  = round(abs(latitude - declination), 1)
    orientation   = "South" if latitude >= 0 else "North"
    peak_sun_hrs  = round(5 + 2 * math.cos(math.radians(latitude)), 2)

    return {
        "optimal_tilt_angle"       : optimal_tilt,
        "optimal_orientation"      : orientation,
        "estimated_peak_sun_hours" : peak_sun_hrs,
        "monthly_energy_estimate_kwh": round(peak_sun_hrs * 5 * 0.85 * 30, 1),
    }


# ─────────────────────────────────────────────
#  5. Quick Test / Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    model = train_model()

    result = predict_output(
        temperature=38, light_intensity=750, dust_level=15,
        tilt_angle=20, hour_of_day=12, cloud_cover=10,
        model=model
    )
    print("\n🔮 Sample Prediction:")
    print(result)

    placement = optimize_placement(latitude=17.38, month=6)
    print("\n📐 Optimal Placement for Hyderabad (June):")
    print(placement)
