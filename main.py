from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil, os, base64
from datetime import datetime

from backend.location import get_nearby_services
from backend.notifier import send_email_notification
from backend.report import generate_report
from backend.model import detect_incident
from backend.severity import calculate_severity
from backend.database import init_db, insert_incident

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ── Serve the frontend HTML at /ui ────────────────────────────────────────
# This makes the frontend served from the same origin as the API
# so there are zero CORS issues and no page refresh problems.
FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')

@app.get("/")
def home():
    return {"message": "Smart City AI Backend Running. Open /ui for the interface."}

@app.get("/ui")
def serve_ui():
    return FileResponse(FRONTEND)


@app.post("/analyze")
async def analyze(
    file:  UploadFile,
    lat:   float = Form(...),
    lon:   float = Form(...),
    email: str   = Form(None),
):
    try:
        # Save file
        path = f"temp_{file.filename}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Detect
        result        = detect_incident(path)
        incident_type = result.get("type",       "Unknown")
        confidence    = result.get("confidence",  None)
        raw_label     = result.get("raw_label",   None)
        all_dets      = result.get("all_detections", [])
        model_ver     = result.get("model_version",  "YOLOv11x")

        # Severity + nearby
        severity = calculate_severity(incident_type)
        nearby   = get_nearby_services(lat, lon)

        # Save to DB
        insert_incident(
            incident_type, severity, lat, lon,
            str(datetime.now()), confidence, raw_label
        )

        # PDF report → base64
        report_path = generate_report(incident_type, severity, lat, lon, nearby)
        report_b64  = None
        report_name = None
        if report_path and os.path.exists(report_path):
            with open(report_path, "rb") as f:
                report_b64  = base64.b64encode(f.read()).decode()
            report_name = os.path.basename(report_path)

        # Email
        notification_sent = False
        if email:
            notification_sent = send_email_notification(
                email, incident_type, severity, lat, lon, nearby
            )

        return {
            "type":              incident_type,
            "severity":          severity,
            "confidence":        confidence,
            "raw_label":         raw_label,
            "all_detections":    all_dets,
            "model_version":     model_ver,
            "lat":               lat,
            "lon":               lon,
            "nearby_services":   nearby,
            "report_b64":        report_b64,
            "report_name":       report_name,
            "notification_sent": notification_sent,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}