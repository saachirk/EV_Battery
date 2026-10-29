from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import serial
import streamlit as st
from serial.tools import list_ports

from train_model import train_and_save_models

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "ev_battery_test_data (1).xlsx"
MODELS_DIR = ROOT / "models"
OUTPUTS_DIR = ROOT / "outputs"

MODEL_A_PATH = MODELS_DIR / "model_a.pkl"
MODEL_B_PATH = MODELS_DIR / "model_b.pkl"
METRICS_PATH = OUTPUTS_DIR / "model_metrics.json"

BATTERY_FEATURES = ["voltage_V", "current_A", "battery_temp_C"]
BATTERY_ENV_FEATURES = [
    "voltage_V",
    "current_A",
    "battery_temp_C",
    "ambient_temp_C",
    "humidity_pct",
]

SCENARIO_VALUES = {
    "Normal": {"voltage_V": 3.75, "current_A": 0.74, "battery_temp_C": 28.9, "ambient_temp_C": 24.4, "humidity_pct": 44.5},
    "High_Battery_Temperature": {"voltage_V": 3.72, "current_A": 1.08, "battery_temp_C": 48.9, "ambient_temp_C": 31.9, "humidity_pct": 55.0},
    "Overvoltage": {"voltage_V": 4.28, "current_A": 0.80, "battery_temp_C": 30.2, "ambient_temp_C": 24.5, "humidity_pct": 41.2},
    "Undervoltage": {"voltage_V": 2.84, "current_A": 0.90, "battery_temp_C": 28.1, "ambient_temp_C": 24.0, "humidity_pct": 42.8},
    "High_Current": {"voltage_V": 3.54, "current_A": 4.90, "battery_temp_C": 34.7, "ambient_temp_C": 28.1, "humidity_pct": 49.8},
    "Hot_Environment": {"voltage_V": 3.69, "current_A": 1.03, "battery_temp_C": 38.5, "ambient_temp_C": 41.9, "humidity_pct": 68.4},
}


def ensure_model_files() -> None:
    if not MODEL_A_PATH.exists() or not MODEL_B_PATH.exists() or not METRICS_PATH.exists():
        train_and_save_models()


@st.cache_data
def load_metrics() -> dict:
    ensure_model_files()
    with METRICS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_resource
def load_model(model_name: str):
    ensure_model_files()
    import joblib

    file_path = MODELS_DIR / f"{model_name}.pkl"
    if not file_path.exists():
        raise FileNotFoundError(f"Missing model file: {file_path}")
    return joblib.load(file_path)


@st.cache_data
def load_dataset_preview() -> pd.DataFrame:
    df = pd.read_excel(DATASET_PATH, sheet_name="Data")
    df = df[["timestamp", "voltage_V", "current_A", "battery_temp_C", "ambient_temp_C", "humidity_pct", "fault_label", "scenario"]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.head(20)


def summarize_condition(value: int) -> str:
    return "Normal" if value == 0 else "Fault detected"


def classify_fault_type(reading: dict) -> tuple[str, str]:
    voltage = reading["voltage"]
    current = reading["current"]
    battery_temp = reading["battery_temp"]
    ambient_temp = reading["ambient_temp"]
    humidity = reading["humidity"]

    if battery_temp >= 45.0:
        return "High_Battery_Temperature", "High"
    if voltage >= 4.1:
        return "Overvoltage", "High"
    if voltage <= 3.0:
        return "Undervoltage", "Medium"
    if current >= 3.0:
        return "High_Current", "High"
    if ambient_temp >= 35.0:
        return "Hot_Environment", "Medium"
    if humidity >= 70.0:
        return "High_Humidity", "Low"
    return "Normal", "Low"


def predict_fault(model_name: str, reading: dict) -> int:
    model = load_model(model_name)
    if model_name == "model_a":
        features = pd.DataFrame([
            {
                "voltage_V": float(reading["voltage"]),
                "current_A": float(reading["current"]),
                "battery_temp_C": float(reading["battery_temp"]),
            }
        ])
    else:
        features = pd.DataFrame([
            {
                "voltage_V": float(reading["voltage"]),
                "current_A": float(reading["current"]),
                "battery_temp_C": float(reading["battery_temp"]),
                "ambient_temp_C": float(reading["ambient_temp"]),
                "humidity_pct": float(reading["humidity"]),
            }
        ])
    pred = model.predict(features)[0]
    return int(pred)


def parse_serial_line(raw_line: str) -> dict | None:
    text = str(raw_line).strip()
    if not text:
        return None
    parts = [item.strip() for item in text.split(",")]
    if len(parts) != 5:
        return None
    try:
        voltage, current, battery_temp, ambient_temp, humidity = [float(value) for value in parts]
    except ValueError:
        return None
    return {
        "voltage": voltage,
        "current": current,
        "battery_temp": battery_temp,
        "ambient_temp": ambient_temp,
        "humidity": humidity,
    }


def add_reading(reading: dict, source: str) -> None:
    entry = {
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "voltage_V": float(reading["voltage"]),
        "current_A": float(reading["current"]),
        "battery_temp_C": float(reading["battery_temp"]),
        "ambient_temp_C": float(reading["ambient_temp"]),
        "humidity_pct": float(reading["humidity"]),
        "source": source,
        "condition": "",
        "fault_type": "",
        "severity": "",
    }

    pred = predict_fault("model_b", reading)
    entry["condition"] = summarize_condition(pred)
    fault_type, severity = classify_fault_type(reading)
    entry["fault_type"] = fault_type
    entry["severity"] = severity

    if "readings" not in st.session_state:
        st.session_state.readings = pd.DataFrame(columns=[
            "timestamp",
            "voltage_V",
            "current_A",
            "battery_temp_C",
            "ambient_temp_C",
            "humidity_pct",
            "source",
            "condition",
            "fault_type",
            "severity",
        ])

    st.session_state.readings = pd.concat(
        [st.session_state.readings, pd.DataFrame([entry])],
        ignore_index=True,
    )


def generate_simulation_reading(scenario_name: str, custom_values: dict | None = None) -> dict:
    if custom_values:
        return {
            "voltage": float(custom_values["voltage_V"]),
            "current": float(custom_values["current_A"]),
            "battery_temp": float(custom_values["battery_temp_C"]),
            "ambient_temp": float(custom_values["ambient_temp_C"]),
            "humidity": float(custom_values["humidity_pct"]),
        }
    defaults = SCENARIO_VALUES[scenario_name]
    return {
        "voltage": defaults["voltage_V"],
        "current": defaults["current_A"],
        "battery_temp": defaults["battery_temp_C"],
        "ambient_temp": defaults["ambient_temp_C"],
        "humidity": defaults["humidity_pct"],
    }


def get_active_reading_for_display(mode: str, slider_values: dict | None = None) -> dict:
    if mode == "Simulation mode":
        if slider_values is None:
            slider_values = {
                "voltage": 3.75,
                "current": 0.74,
                "battery_temp": 28.9,
                "ambient_temp": 24.4,
                "humidity": 44.5,
            }
        return {
            "voltage": float(slider_values["voltage"]),
            "current": float(slider_values["current"]),
            "battery_temp": float(slider_values["battery_temp"]),
            "ambient_temp": float(slider_values["ambient_temp"]),
            "humidity": float(slider_values["humidity"]),
        }

    if "latest_serial_reading" in st.session_state:
        return st.session_state.latest_serial_reading

    if "readings" in st.session_state and not st.session_state.readings.empty:
        latest = st.session_state.readings.iloc[-1]
        return {
            "voltage": float(latest["voltage_V"]),
            "current": float(latest["current_A"]),
            "battery_temp": float(latest["battery_temp_C"]),
            "ambient_temp": float(latest["ambient_temp_C"]),
            "humidity": float(latest["humidity_pct"]),
        }

    return {
        "voltage": 0.0,
        "current": 0.0,
        "battery_temp": 0.0,
        "ambient_temp": 0.0,
        "humidity": 0.0,
    }


def show_comparison_table() -> None:
    metrics = load_metrics()
    comparison = pd.DataFrame(metrics["comparison"])
    display_table = comparison[["model", "accuracy", "precision", "recall", "f1_score"]].copy()
    display_table["accuracy"] = display_table["accuracy"].map(lambda x: round(float(x), 4))
    display_table["precision"] = display_table["precision"].map(lambda x: round(float(x), 4))
    display_table["recall"] = display_table["recall"].map(lambda x: round(float(x), 4))
    display_table["f1_score"] = display_table["f1_score"].map(lambda x: round(float(x), 4))
    st.dataframe(display_table, width="stretch")


# ---------------------------------------------------------------------------
# Streamlit app
# ---------------------------------------------------------------------------

st.set_page_config(page_title="EV Battery Monitor", layout="wide")
st.title("EV Battery Monitoring and Anomaly Detection")
st.caption("Prototype dashboard for battery telemetry, fault detection, and ESP32-ready serial monitoring.")

ensure_model_files()

with st.sidebar:
    st.header("Controls")
    mode = st.radio("Mode", ["Simulation mode", "ESP32 Serial mode"])
    st.caption("For a demo, Simulation mode works without ESP32 hardware.")

    if mode == "Simulation mode":
        scenario = st.selectbox("Simulation scenario", list(SCENARIO_VALUES.keys()))
        st.caption("Simulated values are clearly labelled for demonstration only.")
        custom_voltage = st.slider("Voltage (V)", 2.5, 5.0, round(SCENARIO_VALUES[scenario]["voltage_V"], 2), step=0.01)
        custom_current = st.slider("Current (A)", 0.0, 6.0, round(SCENARIO_VALUES[scenario]["current_A"], 2), step=0.01)
        custom_battery_temp = st.slider("Battery temperature (°C)", 20.0, 60.0, round(SCENARIO_VALUES[scenario]["battery_temp_C"], 2), step=0.1)
        custom_ambient_temp = st.slider("Ambient temperature (°C)", 15.0, 50.0, round(SCENARIO_VALUES[scenario]["ambient_temp_C"], 2), step=0.1)
        custom_humidity = st.slider("Humidity (%)", 25.0, 90.0, round(SCENARIO_VALUES[scenario]["humidity_pct"], 2), step=0.1)

        current_preview = {
            "voltage": custom_voltage,
            "current": custom_current,
            "battery_temp": custom_battery_temp,
            "ambient_temp": custom_ambient_temp,
            "humidity": custom_humidity,
        }
        preview_pred = predict_fault("model_b", current_preview)
        preview_fault, preview_severity = classify_fault_type(current_preview)

        st.markdown("### Live preview")
        st.metric("Voltage (V)", f"{custom_voltage:.2f}")
        st.metric("Current (A)", f"{custom_current:.2f}")
        st.metric("Battery temp (°C)", f"{custom_battery_temp:.2f}")
        st.metric("Ambient temp (°C)", f"{custom_ambient_temp:.2f}")
        st.metric("Humidity (%)", f"{custom_humidity:.2f}")
        if preview_pred == 0:
            st.success(f"Condition: {summarize_condition(preview_pred)}")
        else:
            st.warning(f"Condition: {summarize_condition(preview_pred)} | Fault: {preview_fault} | Severity: {preview_severity}")

        if st.button("Add preview to readings"):
            add_reading(current_preview, "simulated")
            st.success("Selected simulation values were added to the dashboard.")

        st.session_state["latest_simulation_reading"] = current_preview

    else:
        port_list = [port.device for port in list_ports.comports()]
        if not port_list:
            port_list = ["No COM ports detected"]
        chosen_port = st.selectbox("COM port", port_list)
        baud_rate = st.selectbox("Baud rate", [9600, 115200, 57600, 74880])

        connect_button = st.button("Connect")
        disconnect_button = st.button("Disconnect")

        if disconnect_button:
            if "serial_handle" in st.session_state:
                st.session_state.serial_handle.close()
                del st.session_state.serial_handle
            st.caption("Serial connection closed.")

        if connect_button:
            if chosen_port == "No COM ports detected":
                st.error("No USB serial port is detected. Connect the ESP32 and try again.")
            else:
                try:
                    serial_handle = serial.Serial(chosen_port, baud_rate, timeout=1)
                    time.sleep(0.5)
                    st.session_state.serial_handle = serial_handle
                    st.success(f"Connected to {chosen_port} at {baud_rate} baud.")
                except Exception as exc:  # pragma: no cover
                    st.error(f"Unable to open {chosen_port}: {exc}")

        if st.button("Read one serial message"):
            handle = st.session_state.get("serial_handle")
            if handle is None:
                st.warning("No ESP32 serial connection is active.")
            else:
                try:
                    raw_line = handle.readline()
                    if not raw_line:
                        st.warning("No data received. The ESP32 may be disconnected or idle.")
                    else:
                        parsed = parse_serial_line(raw_line.decode("utf-8", errors="replace"))
                        if parsed is None:
                            st.warning(f"Malformed serial data received: {raw_line!r}")
                        else:
                            st.session_state.latest_serial_reading = parsed
                            add_reading(parsed, "serial")
                            st.success("Serial reading accepted and added to the dashboard.")
                except Exception as exc:  # pragma: no cover
                    st.error(f"Serial read failed: {exc}")

        if st.checkbox("Auto-refresh serial readings every 2 seconds"):
            handle = st.session_state.get("serial_handle")
            if handle is None:
                st.warning("Connect to a COM port before enabling auto-refresh.")
            else:
                raw_line = handle.readline()
                if raw_line:
                    parsed = parse_serial_line(raw_line.decode("utf-8", errors="replace"))
                    if parsed is not None:
                        st.session_state.latest_serial_reading = parsed
                        add_reading(parsed, "serial")
                time.sleep(2)
                st.rerun()

    st.markdown("---")
    st.caption("Illustrative safety thresholds for demonstration only. These are not validated battery safety limits.")

if "readings" not in st.session_state:
    initial_frame = load_dataset_preview()
    st.session_state.readings = initial_frame.rename(columns={
        "voltage_V": "voltage_V",
        "current_A": "current_A",
        "battery_temp_C": "battery_temp_C",
        "ambient_temp_C": "ambient_temp_C",
        "humidity_pct": "humidity_pct",
    })
    st.session_state.readings["source"] = "dataset"
    st.session_state.readings["condition"] = ""
    st.session_state.readings["fault_type"] = ""
    st.session_state.readings["severity"] = ""

recent_df = st.session_state.readings.tail(20).copy()
if recent_df.empty:
    recent_df = pd.DataFrame([
        {
            "timestamp": pd.Timestamp.now(),
            "voltage_V": 0.0,
            "current_A": 0.0,
            "battery_temp_C": 0.0,
            "ambient_temp_C": 0.0,
            "humidity_pct": 0.0,
            "source": "empty",
            "condition": "",
            "fault_type": "",
            "severity": "",
        }
    ])

if mode == "Simulation mode":
    slider_values = {
        "voltage": float(custom_voltage),
        "current": float(custom_current),
        "battery_temp": float(custom_battery_temp),
        "ambient_temp": float(custom_ambient_temp),
        "humidity": float(custom_humidity),
    }
    latest_display = get_active_reading_for_display(mode, slider_values)
else:
    latest_display = get_active_reading_for_display(mode)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Voltage (V)", f"{latest_display['voltage']:.2f}")
with col2:
    st.metric("Current (A)", f"{latest_display['current']:.2f}")
with col3:
    st.metric("Battery temp (°C)", f"{latest_display['battery_temp']:.2f}")
with col4:
    st.metric("Ambient temp (°C)", f"{latest_display['ambient_temp']:.2f}")
with col5:
    st.metric("Humidity (%)", f"{latest_display['humidity']:.2f}")

predicted_reading = {
    "voltage": float(latest_display["voltage"]),
    "current": float(latest_display["current"]),
    "battery_temp": float(latest_display["battery_temp"]),
    "ambient_temp": float(latest_display["ambient_temp"]),
    "humidity": float(latest_display["humidity"]),
}

predicted_value = predict_fault("model_b", predicted_reading)
condition = summarize_condition(predicted_value)
fault_type, severity = classify_fault_type(predicted_reading)

st.subheader("Battery condition")
if predicted_value == 0:
    st.success(f"Condition: {condition}")
else:
    st.warning(f"Condition: {condition} | Fault type: {fault_type} | Severity: {severity}")

st.caption("Serial message format: voltage,current,battery_temp,ambient_temp,humidity")

st.subheader("Recent sensor readings")
recent_df_display = recent_df[["timestamp", "voltage_V", "current_A", "battery_temp_C", "ambient_temp_C", "humidity_pct", "source", "condition", "fault_type", "severity"]].reset_index(drop=True)
st.dataframe(recent_df_display, width="stretch")

st.download_button(
    "Export recent readings as CSV",
    data=recent_df_display.to_csv(index=False),
    file_name="battery_readings.csv",
    mime="text/csv",
)

st.subheader("Voltage and temperature trend")
chart_df = recent_df[["timestamp", "voltage_V", "battery_temp_C"]].rename(columns={"timestamp": "time"})
chart_df = chart_df.set_index("time")
st.line_chart(chart_df)

st.subheader("Model comparison")
show_comparison_table()

st.subheader("Confusion matrix")
metrics = load_metrics()
for item in metrics["comparison"]:
    st.write(item["model"])
    st.json({
        "accuracy": item["accuracy"],
        "precision": item["precision"],
        "recall": item["recall"],
        "f1_score": item["f1_score"],
        "confusion_matrix": item["confusion_matrix"],
    })

st.markdown("---")
st.caption("This prototype uses the dataset in the project root and is designed for demonstration. It is not a validated battery safety diagnosis system.")
