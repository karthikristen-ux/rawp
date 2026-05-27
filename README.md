# ☢️ Radioactive Water Predictor

### Real-Time Water Quality Monitoring & Radioactive Contamination Detection System

> Built by **Karthikeyan** | ESP32 + TDS Sensor Hardware | Flask + Chart.js Dashboard | Gmail NGO Alerts

---

## 🧠 What is This Project?

This is a **real-time water safety monitoring system** that detects potential radioactive contamination in water. It works like this:

1. An **ESP32 microcontroller** with a **TDS (Total Dissolved Solids) sensor** is dipped into a water sample
2. The ESP32 reads the TDS value and sends it to a **Flask web server** running on your laptop over WiFi
3. The server uses **chemistry-based formulas** to derive 7 other water quality parameters (pH, hardness, nitrate, sulfate, chloride, conductivity, turbidity) from the single TDS reading
4. Based on all these values, the system **predicts which radioactive element** is likely present (Radon, Radium, Uranium, Strontium, or Cesium) and calculates a **risk score (0-100%)**
5. All results are shown on a beautiful **real-time web dashboard** with animated gauges, charts, and comparison against WHO safe limits
6. If dangerous contamination is detected, you can **send a formatted email report** to nearby NGOs / health authorities with one click

You can also use **Manual Mode** (no hardware needed) to enter TDS values by hand and test the system.

---

## 🏗️ System Architecture

```
┌─────────────────────┐        WiFi (HTTP POST)        ┌────────────────────────┐
│                     │ ─────────────────────────────►  │                        │
│   ESP32 DevKit V1   │   Sends TDS value every 5s     │   Flask Backend        │
│   + TDS Sensor      │   to /api/sensor                │   (app.py)             │
│   (in the water)    │                                 │                        │
└─────────────────────┘                                 └────────┬───────────────┘
                                                                 │
                                                    ┌────────────┼────────────┐
                                                    ▼            ▼            ▼
                                              ┌──────────┐ ┌──────────┐ ┌──────────┐
                                              │Chemistry │ │Dashboard │ │NGO Alert │
                                              │Prediction│ │ (HTML/   │ │ (Gmail   │
                                              │ Engine   │ │  JS/CSS) │ │  SMTP)   │
                                              └──────────┘ └──────────┘ └──────────┘
```

---

## 📁 Project File Structure (What Each File Does)

```
radioactivewater-tester-main/
│
├── app.py                          # 🖥️  The MAIN Flask web server
│                                   #     - Receives TDS data from ESP32 via /api/sensor
│                                   #     - Runs prediction engine on each reading
│                                   #     - Serves the dashboard webpage
│                                   #     - Handles manual analysis (/api/analyze)
│                                   #     - Sends NGO alerts (/api/alert)
│                                   #     - Saves all data to water_data.csv
│
├── prediction_engine.py            # 🧪  The brain of the system
│                                   #     - Derives pH, hardness, nitrate etc. from TDS
│                                   #     - Detects which radioactive element is likely present
│                                   #     - Calculates risk score (0-100%)
│                                   #     - Compares values against WHO safe limits
│
├── alert_system.py                 # 📧  Email/SMS notification system
│                                   #     - Sends beautiful HTML email reports to NGOs
│                                   #     - Uses Gmail SMTP (configured in config.py)
│                                   #     - Optional Twilio SMS fallback
│
├── config.py                       # ⚙️  All settings in one place
│                                   #     - Gmail credentials for sending alerts
│                                   #     - Default NGO email addresses
│                                   #     - Server port, sensor timeout, WHO safe ranges
│
├── requirements.txt                # 📦  Python packages needed (flask, pandas, etc.)
│
├── water_data.csv                  # 📊  Auto-generated CSV of all readings
│                                   #     - Every test (manual or ESP32) is saved here
│                                   #     - Columns: Timestamp, Location, TDS, pH, Hardness,
│                                   #       Nitrate, Sulfate, Chloride, Conductivity,
│                                   #       Turbidity, RiskScore, Element, Isotope
│
├── esp32_firmware/
│   └── tds_sensor.ino              # 🔌  Arduino code for the ESP32
│                                   #     - Connects to WiFi
│                                   #     - Reads TDS sensor on GPIO 34
│                                   #     - Sends readings to Flask server via HTTP POST
│                                   #     - Auto-reconnects on WiFi drop
│
├── templates/
│   └── index.html                  # 🌐  Dashboard webpage (served by Flask)
│
├── static/
│   ├── css/
│   │   └── dashboard.css           # 🎨  Dark glassmorphism theme with neon accents
│   └── js/
│       └── dashboard.js            # ⚡  Real-time gauges, charts, polling, auto-location
│
└── radioactive_process.png         # 🖼️  Awareness image used in the dashboard
```

---

## 🧪 The Science: How We Predict Radioactive Elements from TDS

### Why TDS?
TDS (Total Dissolved Solids) measures the total concentration of dissolved substances in water — minerals, salts, metals, etc. Radioactive elements like Uranium and Radium are heavy metals that dissolve into groundwater from rock formations. **Higher TDS = more dissolved minerals = higher chance of radioactive contamination.**

### Chemistry Formulas Used

Since we only have a TDS sensor (which is cheap: ₹200-400), we use established water chemistry correlations to **estimate** the other parameters:

| Parameter | Formula | Why This Works |
|-----------|---------|----------------|
| **Conductivity** (µS/cm) | `TDS / 0.65` | Standard conversion factor. Water's ability to conduct electricity is directly proportional to its dissolved ions. |
| **pH** | `7.0 + (TDS - 300) × 0.002` | Pure water is pH 7. Higher TDS means more dissolved alkaline minerals (Ca²⁺, Mg²⁺), which push pH slightly alkaline. |
| **Hardness** (mg/L CaCO₃) | `TDS × 0.40` | ~40% of dissolved solids in groundwater are hardness-causing minerals (Calcium + Magnesium ions). |
| **Nitrate** (mg/L NO₃⁻) | `TDS × 0.05` | ~5% of TDS. Correlates with agricultural runoff containing nitrogen fertilizers. |
| **Sulfate** (mg/L SO₄²⁻) | `TDS × 0.15` | ~15% of dissolved solids. Sulfate minerals are common in mineral-rich groundwater. |
| **Chloride** (mg/L Cl⁻) | `TDS × 0.20` | ~20% of TDS. Chloride is one of the most common dissolved ions in water. |
| **Turbidity** (NTU) | `(TDS - 200) × 0.02` | Higher dissolved solids correlate with more suspended particles (cloudiness). |

> **Note:** The system adds ±5% random noise to simulate realistic sensor variation, so values aren't unrealistically exact.

### Radioactive Element Detection Logic

Based on TDS levels, the system identifies the most probable radioactive contaminant:

| TDS Range (mg/L) | Element | Isotope | Why |
|-------------------|---------|---------|-----|
| 0 – 200 | **None** | — | Clean water, very few dissolved minerals |
| 200 – 500 | **Radon** | ²²²Rn | Dissolved radioactive gas, common in granite bedrock groundwater |
| 500 – 800 | **Radium** | ²²⁶Ra | Correlates with high mineral/hardness content in deep wells |
| 800 – 1200 | **Uranium** | ²³⁸U | Heavy mineral dissolution from uranium-bearing rock formations |
| 1200 – 1600 | **Strontium** | ⁹⁰Sr | Nuclear fission product, marker of nuclear fallout |
| 1600+ | **Cesium** | ¹³⁷Cs | Indicates severe nuclear contamination (reactor accidents) |

### Risk Score Calculation (0–100%)

The risk score is a weighted sum:
- **TDS** exceeding 500 mg/L → contributes up to **25 points**
- **pH** deviating from 7.0 → contributes up to **20 points**
- **Hardness** exceeding 200 mg/L → contributes up to **20 points**
- **Nitrate** exceeding 45 mg/L → contributes up to **20 points**
- **Sulfate + Chloride** exceeding 250 mg/L each → contributes up to **15 points**

---

## 🔌 Hardware Details

### Components
| Component | What It Does | Cost |
|-----------|-------------|------|
| ESP32 DevKit V1 | WiFi-enabled microcontroller, reads sensor & sends data | ₹350–500 |
| TDS Sensor Module (e.g., DFRobot SEN0244) | Measures dissolved solids in water via two metal probes | ₹200–400 |
| Jumper Wires (3 pieces) | Connect sensor to ESP32 | ₹30 |
| Micro-USB Cable | Power & program the ESP32 | ₹50 |

### Wiring (3 wires only!)
```
TDS Sensor Pin          ESP32 Pin
──────────────          ─────────
     VCC      ────────►   5V (or VIN)
     GND      ────────►   GND
     SIG      ────────►   GPIO 34 (Analog Input)
```

### How the TDS Sensor Works in the Arduino Code
1. Takes **30 ADC readings** and sorts them (median filtering removes noise/outliers)
2. Averages the middle 60% of samples
3. Converts ADC value → voltage: `voltage = ADC × 3.3 / 4096`
4. Applies **temperature compensation** (reference: 25°C): `compensatedV = voltage / (1 + 0.02 × (temp - 25))`
5. Converts voltage → TDS using the standard polynomial formula:
   ```
   TDS = (133.42 × V³ - 255.86 × V² + 857.39 × V) × 0.5
   ```

---

## 🖥️ API Endpoints (How the Backend Works)

| Endpoint | Method | What It Does |
|----------|--------|-------------|
| `/` | GET | Serves the dashboard webpage |
| `/api/sensor` | POST | Receives TDS from ESP32. Body: `{"tds": 450}` |
| `/api/analyze` | POST | Manual analysis. Body: `{"tds": 750, "location": "Lab", "ph": 7.5}` |
| `/api/latest` | GET | Returns the latest reading with full analysis |
| `/api/readings` | GET | Returns all historical readings as JSON |
| `/api/set-location` | POST | Set location for ESP32 readings. Body: `{"location": "Chennai"}` |
| `/api/alert` | POST | Send email report to NGO. Body: `{"email": "ngo@example.com"}` |
| `/api/alerts` | GET | Returns history of sent alerts |
| `/api/status` | GET | ESP32 connection status |
| `/api/download` | GET | Download water_data.csv file |

---

## 🚀 HOW TO RUN THIS ON YOUR LAPTOP

### Prerequisites
- **Python 3.8+** installed ([Download here](https://www.python.org/downloads/))
- **Git** (optional, to clone the repo)
- A **web browser** (Chrome, Edge, Firefox — anything works)

### Step 1: Get the Project Files
Either your friend gives you the folder, or clone from GitHub:
```bash
git clone <repo-url>
cd radioactivewater-tester-main
```

### Step 2: Install Python Dependencies
Open a terminal/command prompt **in the project folder** and run:
```bash
pip install -r requirements.txt
```
This installs: Flask, Flask-CORS, Pandas, NumPy, Plotly, Twilio

### Step 3: Run the Server
```bash
python app.py
```
You'll see output like:
```
============================================================
  [*] RADIOACTIVE WATER PREDICTOR - SERVER
============================================================
  Dashboard:  http://localhost:5000
  Network:    http://192.168.1.105:5000
  ESP32 API:  http://192.168.1.105:5000/api/sensor

  Set this IP in your ESP32 Arduino code:
    const char* serverIP = "192.168.1.105";
============================================================
```

### Step 4: Open the Dashboard
Open your browser and go to: **http://localhost:5000**

### Step 5: Test Without Hardware
1. On the dashboard, you'll see **Manual Mode** is selected by default
2. Enter a TDS value (try 450, 750, 1100, or 1800 to see different elements detected)
3. Click the **📍 button** next to Location to auto-detect your GPS location
4. Click **"⚡ Run Analysis"**
5. Watch the gauge, element card, parameter grid, and comparison chart update!

### Step 6: (Optional) Connect ESP32 Hardware
1. Install **Arduino IDE** from https://www.arduino.cc/en/software
2. Add ESP32 board support:
   - `File → Preferences → Board Manager URLs` → add:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - `Tools → Board → Board Manager` → search "ESP32" → Install
3. Open `esp32_firmware/tds_sensor.ino` in Arduino IDE
4. **Change these 3 lines:**
   ```cpp
   const char* WIFI_SSID = "YOUR_WIFI_NAME";       // Your WiFi name
   const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";    // Your WiFi password
   const char* SERVER_IP = "192.168.1.105";         // Your laptop's IP (from Step 3 output)
   ```
5. Wire the TDS sensor (3 wires — see Wiring section above)
6. Select board: `Tools → Board → ESP32 Dev Module`
7. Select port: `Tools → Port → COM__` (your ESP32's port)
8. Click **Upload** ▶️
9. On the dashboard, switch to **🔌 ESP32 Mode**, set the location, and watch live data flow in!

---

## 🔄 Running on a DIFFERENT Laptop (WiFi Portability)

The ESP32 connects to your **WiFi router**, NOT directly to any laptop. So you can run the server on any laptop connected to the same WiFi.

### Quick Steps:
1. Copy the entire `radioactivewater-tester-main` folder to the new laptop (USB drive, Google Drive, whatever)
2. Install Python + dependencies: `pip install -r requirements.txt`
3. Run: `python app.py`
4. Note the **Network IP** from the terminal output (e.g., `192.168.1.110`)
5. If using ESP32 hardware:
   - Open `tds_sensor.ino` in Arduino IDE
   - Change `SERVER_IP` to the new laptop's IP
   - Re-upload to ESP32
6. Open `http://localhost:5000` on the new laptop — done!

### Pro Tip: Use a Static IP
So you don't have to change the ESP32 code every time:
1. On your laptop: **Settings → Network → WiFi → Your Network → IP Settings → Manual**
2. Set IP to something like `192.168.1.200`, Subnet: `255.255.255.0`, Gateway: `192.168.1.1`
3. Use `192.168.1.200` in the ESP32 code — it never changes!

### Key Rules:
- ✅ ESP32 and laptop MUST be on the **same WiFi network**
- ✅ The Flask server binds to `0.0.0.0` so it's accessible from ANY device on the network
- ✅ You can open the dashboard from a **phone/tablet** too: `http://<laptop-ip>:5000`

---

## 📧 Email Alert Configuration

The system sends beautiful HTML email reports to NGOs. Currently configured:
- **Sender:** `autismscreening18@gmail.com` (Gmail SMTP)
- **Default Recipient:** `karthikristen@gmail.com`
- **Custom Recipient:** You can type any email on the dashboard before sending

To change the sender email, edit `config.py`:
```python
GMAIL_USER = "your-email@gmail.com"
GMAIL_APP_PASSWORD = "your-16-char-app-password"
```

To get a Gmail App Password:
1. Enable 2-Step Verification on your Google Account
2. Go to https://myaccount.google.com/apppasswords
3. Generate a password for "Mail"

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Hardware | ESP32 + TDS Sensor | Read water quality |
| Firmware | Arduino C++ | Sensor reading + WiFi + HTTP |
| Backend | Python Flask | REST API + data processing |
| Prediction | Python (custom) | Chemistry formulas + risk scoring |
| Frontend | HTML + CSS + JS | Dashboard UI |
| Charts | Chart.js | Comparison bar charts |
| Styling | Vanilla CSS (Glassmorphism) | Premium dark theme |
| Fonts | Google Fonts (Inter, Orbitron) | Modern typography |
| Location | Browser Geolocation + OpenStreetMap | GPS auto-detect |
| Email | Gmail SMTP (smtplib) | NGO alert reports |
| Data Storage | CSV (pandas) | water_data.csv |

---

## 👨‍💻 Developed by Karthikeyan
