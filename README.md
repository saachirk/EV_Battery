# Edge-Based Electric Vehicle Battery Monitoring and Anomaly Detection

This project is a beginner-friendly prototype for a battery monitoring dashboard that can run in two modes:

- Simulation mode: works without hardware and demonstrates normal and faulty conditions.
- ESP32 Serial mode: reads live values from a microcontroller over USB serial.

The project uses:

- Python
- Streamlit for the dashboard
- Pandas and NumPy for data handling
- Scikit-learn Decision Tree Classifier for fault detection
- PySerial for USB serial communication
- Arduino C++ prototype firmware for ESP32

## Project files

- `app.py` — Streamlit dashboard
- `train_model.py` — loads the dataset, trains the models, and saves the trained objects
- `esp32_firmware.ino` — Arduino sketch template for ESP32
- `requirements.txt` — Python dependencies
- `ev_battery_test_data (1).xlsx` — original Excel dataset in the project root
- `models/` — saved trained models
- `outputs/` — saved evaluation metrics and exported csv files

## 1) Install dependencies on Windows PowerShell

```powershell
cd C:\EV_Vehicle
python -m pip install -r requirements.txt
```

If needed, install directly:

```powershell
cd C:\EV_Vehicle
python -m pip install pandas numpy scikit-learn streamlit pyserial openpyxl joblib
```

## 2) Train the models

```powershell
cd C:\EV_Vehicle
python train_model.py
```

This script reads the dataset from `ev_battery_test_data (1).xlsx`, trains two Decision Tree models, and saves them to `models/`.

## 3) Start the dashboard

```powershell
cd C:\EV_Vehicle
python -m streamlit run app.py
```

Then open the local URL shown in the terminal, usually:

- http://localhost:8501

## 4) Dashboard usage

### Simulation mode

1. Choose `Simulation mode` in the sidebar.
2. Pick a scenario such as `Normal`, `Overvoltage`, `High_Current`, etc.
3. Adjust the slider values or use the scenario defaults.
4. Click `Generate simulated reading`.
5. The dashboard will display:
   - voltage
   - current
   - battery temperature
   - ambient temperature
   - humidity
   - predicted condition
   - fault type and severity
   - recent table and graphs

This mode works without any ESP32 or sensors.

### ESP32 Serial mode

1. Connect the ESP32 to the PC over USB.
2. In the sidebar, choose `ESP32 Serial mode`.
3. Select the COM port and baud rate.
4. Click `Connect`.
5. Click `Read one serial message` or enable auto-refresh.
6. The app expects one line per reading in this format:

```text
voltage,current,battery_temperature,ambient_temperature,humidity
```

Example:

```text
3.72,8.0,32.0,28.0,55.0
```

The dashboard parses the values, predicts the battery condition, and updates the table and charts.

## 5) Serial message format

The dashboard expects this exact order:

1. voltage (V)
2. current (A)
3. battery temperature (°C)
4. ambient temperature (°C)
5. humidity (%)

The message must be a single comma-separated line.

## 6) ESP32 firmware notes

The Arduino sketch is in `esp32_firmware.ino`.

Important safety note:

- Do not connect an EV battery directly to an ESP32 GPIO pin.
- Use a proper safe voltage divider or analog front end for voltage measurement.
- Use a suitable current sensor such as a shunt + amplifier or hall-effect current sensor.
- Confirm the exact hardware pins and libraries before real use.

This file is intentionally written as a prototype template because the actual hardware is not available in this workspace.

## 7) Dataset information

The project uses the real Excel workbook already present in the root folder:

- `ev_battery_test_data (1).xlsx`

The actual dataset columns are:

- `sample_id`
- `timestamp`
- `voltage_V`
- `current_A`
- `battery_temp_C`
- `ambient_temp_C`
- `humidity_pct`
- `scenario`
- `fault_label`
- `fault_type`

The target label is `fault_label` and the values are:

- `0` = Normal
- `1` = Fault present

The data is synthetic illustrative data for software demonstration. It should not be treated as battery safety validation data.

## 8) Model comparison

Two models are trained on the same split:

- Model A: battery voltage, current, battery temperature
- Model B: voltage, current, battery temperature, ambient temperature, humidity

The dashboard shows accuracy, precision, recall, F1-score, and confusion matrix information for both models.

## 9) CSV export

The dashboard includes a CSV export button for the recent readings.

## 10) Demo procedure

1. Install requirements.
2. Run `python train_model.py`.
3. Run `python -m streamlit run app.py`.
4. Open the page in the browser.
5. Use `Simulation mode` to test the dashboard.
6. Switch to `ESP32 Serial mode` when hardware is available.
7. Connect to the ESP32 COM port and start reading serial data.

## 11) Important note

This is a prototype for demonstration and learning. It is not a validated battery safety system and should not be used for real safety-critical diagnosis without proper engineering validation and hardware testing.
