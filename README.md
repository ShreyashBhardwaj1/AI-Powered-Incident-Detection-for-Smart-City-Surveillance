# ⚡ Smart City Sentinel
### AI-Powered Incident Detection & Emergency Response Dispatch for Smart Cities

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![YOLOv11](https://img.shields.io/badge/YOLOv11-Ultralytics-blue?style=for-the-badge&logo=yolo)](https://github.com/ultralytics/ultralytics)
[![Leaflet](https://img.shields.io/badge/Leaflet-JS-green?style=for-the-badge&logo=leaflet)](https://leafletjs.com/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF-orange?style=for-the-badge)](https://www.reportlab.com/)

**Smart City Sentinel** is a state-of-the-art AI-powered incident detection and emergency response system. It automates city surveillance by detecting critical public safety incidents (fires, road accidents, flooding, public disturbances, road damage, and illegal dumping) in real time using Computer Vision, logging the data, locating nearest emergency services (Hospitals & Police), generating official PDF reports, and broadcasting instant email alerts to authorities.

---

## 🌟 Key Features

*   **🧠 YOLOv11x Computer Vision Model:** Leverages the latest extra-large YOLOv11 model for high-accuracy object detection on images and videos, mapping them into specific incident categories (e.g. Fire, Flood, Road Accident).
*   **📍 Live Browser Geolocation:** Automatically detects the reporter's GPS coordinates using the web browser's Geolocation API and pins the incident on an interactive, dark-themed Leaflet.js map.
*   **🏥 Overpass API Emergency Search:** Queries OpenStreetMap (OSM) in real-time to find hospitals and police stations within a **3 km radius**, with automatic mirror switching and Nominatim fallbacks for maximum resilience.
*   **📄 Automated A4 PDF Report Generation:** Instantly creates professional, structured A4 PDF incident reports containing coordinates, severity badges, recommended actions, and closest hospital/police station tables.
*   **📧 SMTP Instant Email Notifications:** Dispatches detailed HTML-formatted email alerts to emergency responders, containing immediate actions, directions, and direct Google Maps navigation links.
*   **🗄️ Hybrid Database Layer:** Logs all incidents in a local SQLite database for offline usage, with native support for cloud databases (PostgreSQL, Supabase, Neon, Railway) by setting a `DATABASE_URL` environment variable.

---

## 📁 Repository Structure

```text
├── database.py       # SQL database wrapper (supports SQLite & PostgreSQL)
├── location.py       # OpenStreetMap Overpass & Nominatim integration
├── notifier.py       # SMTP Email dispatch logic with HTML formatting
├── report.py         # PDF Report generator utilizing ReportLab Flowables
├── model.py          # YOLOv11x inference engine for images/videos
├── severity.py       # Incident severity calculation heuristics
├── utils.py          # Helper functions and utilities
├── main.py           # FastAPI entrypoint exposing APIs & serving UI
├── index.html        # Glassmorphic, dark-mode front-end dashboard
├── requirements.txt  # Python packages required
└── yolov8n.pt        # Preloaded object detection weights (optional)
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/ShreyashBhardwaj1/AI-Powered-Incident-Detection-for-Smart-City-Surveillance.git
cd AI-Powered-Incident-Detection-for-Smart-City-Surveillance
```

### 2. Install dependencies
Ensure you have Python 3.10+ installed. Install all required packages:
```bash
pip install -r requirements.txt
pip install reportlab requests psycopg2-binary
```

### 3. Configure Email Alerts
1. Open [notifier.py](file:///c:/Users/Shrey/OneDrive/Desktop/Study%20material%20AI&DS/Projects/smart_city-main/notifier.py).
2. Update the `SMTP_USER` and `SMTP_PASSWORD` variables:
   ```python
   SMTP_USER     = "your-gmail@gmail.com"
   SMTP_PASSWORD = "your-16-char-gmail-app-password"
   ```
   *(Note: You must generate a 16-character App Password under your Google Account Account Security > App Passwords settings)*

---

## 🚀 Running the Application

Because the project uses package imports (e.g. `from backend.xxx import yyy`), the directory must be treated as a package. You can launch it using one of the following methods:

### Method A: Running as a Python Module (Recommended)
From the directory **containing** `smart_city-main` (the parent folder):
1. Rename the `smart_city-main` directory to `backend`.
2. Run Uvicorn from the parent directory:
   ```bash
   uvicorn backend.main:app --reload
   ```

### Method B: Setting the Python Path
Alternatively, from inside the `smart_city-main` directory:
```bash
# On Windows (PowerShell):
$env:PYTHONPATH="."
uvicorn main:app --reload

# On Linux/macOS:
export PYTHONPATH="."
uvicorn main:app --reload
```

Open your browser and navigate to:
*   **Web Dashboard:** `http://localhost:8000/ui`
*   **FastAPI Swagger Docs:** `http://localhost:8000/docs`

---

## 🛠️ Technology Stack

*   **Backend:** FastAPI (Python), Uvicorn
*   **Machine Learning:** PyTorch, Ultralytics YOLOv11x / YOLOv8
*   **Database:** SQLite / PostgreSQL (psycopg2)
*   **APIs & Data:** Overpass API (OpenStreetMap), Nominatim API
*   **Frontend:** Vanilla HTML5, CSS3 Grid/Flexbox, Javascript (ES6), Leaflet.js (Map styling via custom filters)
*   **Reporting:** ReportLab PDF toolkit

---

## ⚖️ License
This project is licensed under the MIT License. See the LICENSE file for details.

