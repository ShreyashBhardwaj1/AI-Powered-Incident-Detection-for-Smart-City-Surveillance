"""
backend/notifier.py
Sends an incident-alert e-mail via SMTP (Gmail-ready, no dotenv needed).

HOW TO SET UP GMAIL:
1. Enable 2-Factor Authentication on your Google account
2. Go to: https://myaccount.google.com/apppasswords
3. Create an App Password (select "Mail" + "Windows Computer")
4. Paste the 16-character password as SMTP_PASSWORD below
"""

import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── HARDCODE YOUR CREDENTIALS HERE (no dotenv needed) ──────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "bhavyakaushik04@gmail.com"      # <-- change this
SMTP_PASSWORD = "mxfo dsmr cpwy csoe"       # <-- 16-char Gmail App Password
# ───────────────────────────────────────────────────────────────────────────

_SEVERITY_COLOR = {
    "Low":      "#22c55e",
    "Medium":   "#f59e0b",
    "High":     "#ef4444",
    "Critical": "#7c3aed",
}
_SEVERITY_EMOJI = {
    "Low":      "🟢",
    "Medium":   "🟡",
    "High":     "🔴",
    "Critical": "🚨",
}

# What to do for each incident type
_INCIDENT_ACTIONS = {
    "fire": {
        "icon": "🔥",
        "title": "Fire Detected",
        "actions": [
            "Call Fire Department immediately (101)",
            "Evacuate the area and keep bystanders at a safe distance",
            "Do NOT use water on electrical fires — use sand or CO₂ extinguisher",
            "Alert nearest hospital for potential burn victims",
        ],
        "authority": "Fire Brigade — 101",
    },
    "accident": {
        "icon": "🚗",
        "title": "Road Accident",
        "actions": [
            "Call ambulance immediately (108)",
            "Do not move injured persons unless there is immediate danger",
            "Call police to manage traffic and file FIR (100)",
            "Keep the scene clear for emergency vehicles",
        ],
        "authority": "Police — 100 | Ambulance — 108",
    },
    "flood": {
        "icon": "🌊",
        "title": "Flooding Detected",
        "actions": [
            "Alert NDRF / local disaster management authority",
            "Evacuate low-lying areas immediately",
            "Turn off electrical mains in flooded areas",
            "Move to higher ground and avoid walking in flowing water",
        ],
        "authority": "NDRF — 011-24363260",
    },
    "fight": {
        "icon": "⚠️",
        "title": "Public Disturbance / Fight",
        "actions": [
            "Call police immediately (100)",
            "Do not intervene physically",
            "Keep a safe distance and document if safe to do so",
            "Alert nearby security personnel",
        ],
        "authority": "Police — 100",
    },
    "pothole": {
        "icon": "🕳️",
        "title": "Road Damage / Pothole",
        "actions": [
            "Report to Municipal Corporation / PWD department",
            "Place warning signs or alert nearby traffic",
            "Document with photos for official complaint",
        ],
        "authority": "Municipal Helpline — 1533",
    },
    "garbage": {
        "icon": "🗑️",
        "title": "Illegal Dumping / Garbage",
        "actions": [
            "Report to Municipal Sanitation Department",
            "Avoid contact — may contain hazardous waste",
            "File complaint on Swachh Bharat app or 1969",
        ],
        "authority": "Sanitation Helpline — 1969",
    },
}

_DEFAULT_ACTION = {
    "icon": "⚠️",
    "title": "Incident Detected",
    "actions": [
        "Contact local authorities immediately",
        "Ensure public safety in the area",
        "Document the incident for official reporting",
        "Notify emergency services if required",
    ],
    "authority": "Emergency — 112",
}


def _get_incident_info(incident_type: str) -> dict:
    """Match incident type string to action template (case-insensitive)."""
    lower = incident_type.lower()
    for key, val in _INCIDENT_ACTIONS.items():
        if key in lower:
            return val
    return _DEFAULT_ACTION


def _build_html(incident_type, severity, lat, lon, nearby):
    color   = _SEVERITY_COLOR.get(severity, "#6b7280")
    emoji   = _SEVERITY_EMOJI.get(severity, "⚠️")
    info    = _get_incident_info(incident_type)
    maps_link = f"https://www.google.com/maps?q={lat},{lon}"

    # Action items
    action_rows = "".join(
        f"<li style='margin-bottom:6px'>{a}</li>" for a in info["actions"]
    )

    # Hospital rows
    hospital_rows = ""
    for h in nearby.get("hospitals", []):
        h_link = f"https://www.google.com/maps?q={h['lat']},{h['lon']}"
        hospital_rows += (
            f"<tr><td style='padding:6px 12px'>{h['name']}</td>"
            f"<td style='padding:6px 12px'>{h['distance_km']} km</td>"
            f"<td style='padding:6px 12px'><a href='{h_link}' style='color:#3b82f6'>Directions</a></td></tr>"
        )
    if not hospital_rows:
        hospital_rows = "<tr><td colspan='3' style='padding:8px 12px;color:#9ca3af'>None found within 3 km</td></tr>"

    # Police rows
    police_rows = ""
    for p in nearby.get("police", []):
        p_link = f"https://www.google.com/maps?q={p['lat']},{p['lon']}"
        police_rows += (
            f"<tr><td style='padding:6px 12px'>{p['name']}</td>"
            f"<td style='padding:6px 12px'>{p['distance_km']} km</td>"
            f"<td style='padding:6px 12px'><a href='{p_link}' style='color:#3b82f6'>Directions</a></td></tr>"
        )
    if not police_rows:
        police_rows = "<tr><td colspan='3' style='padding:8px 12px;color:#9ca3af'>None found within 3 km</td></tr>"

    table_head = """
      <tr style='background:#e5e7eb;text-align:left'>
        <th style='padding:8px 12px'>Name</th>
        <th style='padding:8px 12px'>Distance</th>
        <th style='padding:8px 12px'>Directions</th>
      </tr>"""

    return f"""
<html><body style="font-family:Arial,sans-serif;background:#f3f4f6;padding:32px;margin:0">
<div style="max-width:620px;margin:auto;background:#fff;border-radius:14px;
            overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)">

  <!-- Header -->
  <div style="background:{color};padding:28px 32px">
    <div style="font-size:32px;margin-bottom:6px">{info['icon']}</div>
    <h1 style="margin:0;color:#fff;font-size:20px;font-weight:700">
      Smart City Incident Alert
    </h1>
    <p style="margin:4px 0 0;color:rgba(255,255,255,.8);font-size:13px">
      {emoji} {severity} Severity — Immediate Action Required
    </p>
  </div>

  <div style="padding:28px 32px">

    <!-- Incident Details -->
    <table style="width:100%;border-collapse:collapse;margin-bottom:24px">
      <tr>
        <td style="padding:9px 0;color:#6b7280;font-size:13px;width:140px">Incident Type</td>
        <td style="padding:9px 0;font-weight:700;font-size:14px">{incident_type}</td>
      </tr>
      <tr style="border-top:1px solid #f3f4f6">
        <td style="padding:9px 0;color:#6b7280;font-size:13px">Severity</td>
        <td style="padding:9px 0">
          <span style="background:{color};color:#fff;padding:3px 12px;
                       border-radius:999px;font-size:12px;font-weight:700">
            {severity}
          </span>
        </td>
      </tr>
      <tr style="border-top:1px solid #f3f4f6">
        <td style="padding:9px 0;color:#6b7280;font-size:13px">Location</td>
        <td style="padding:9px 0;font-size:13px">
          {lat:.5f}, {lon:.5f} &nbsp;
          <a href="{maps_link}" style="color:#3b82f6;font-size:12px">View on Maps ↗</a>
        </td>
      </tr>
      <tr style="border-top:1px solid #f3f4f6">
        <td style="padding:9px 0;color:#6b7280;font-size:13px">Contact Authority</td>
        <td style="padding:9px 0;font-weight:600;color:{color};font-size:13px">
          {info['authority']}
        </td>
      </tr>
    </table>

    <!-- Recommended Actions -->
    <div style="background:#fafafa;border-left:4px solid {color};
                border-radius:6px;padding:16px 20px;margin-bottom:24px">
      <h3 style="margin:0 0 10px;font-size:14px;color:#111">
        ✅ Recommended Immediate Actions
      </h3>
      <ul style="margin:0;padding-left:18px;font-size:13px;color:#374151;line-height:1.7">
        {action_rows}
      </ul>
    </div>

    <!-- Hospitals -->
    <h3 style="margin:0 0 10px;font-size:14px">🏥 Nearest Hospitals</h3>
    <table style="width:100%;border-collapse:collapse;background:#f9fafb;
                  border-radius:8px;margin-bottom:20px;font-size:13px">
      <thead>{table_head}</thead>
      <tbody>{hospital_rows}</tbody>
    </table>

    <!-- Police -->
    <h3 style="margin:0 0 10px;font-size:14px">🚔 Nearest Police Stations</h3>
    <table style="width:100%;border-collapse:collapse;background:#f9fafb;
                  border-radius:8px;font-size:13px">
      <thead>{table_head}</thead>
      <tbody>{police_rows}</tbody>
    </table>

  </div>

  <!-- Footer -->
  <div style="background:#f9fafb;padding:14px 32px;font-size:11px;color:#9ca3af;
              border-top:1px solid #e5e7eb">
    Smart City Incident Detection System &nbsp;|&nbsp; Automated Alert &nbsp;|&nbsp;
    Do not reply to this e-mail.
  </div>
</div>
</body></html>
"""


def send_email_notification(to_email, incident_type, severity, lat, lon, nearby) -> bool:
    """Send HTML alert email. Returns True on success."""

    # Check credentials are set
    if "your_email" in SMTP_USER or "xxxx" in SMTP_PASSWORD:
        print("[notifier] ❌ SMTP credentials not configured in notifier.py")
        print("           → Open backend/notifier.py and set SMTP_USER and SMTP_PASSWORD")
        return False

    if not to_email or "@" not in to_email:
        print(f"[notifier] ❌ Invalid email address: '{to_email}'")
        return False

    try:
        print(f"[notifier] Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 [{severity}] Incident Alert: {incident_type}"
        msg["From"]    = SMTP_USER
        msg["To"]      = to_email

        html = _build_html(incident_type, severity, lat, lon, nearby)
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.set_debuglevel(0)     # set to 1 to see raw SMTP conversation
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        print(f"[notifier] ✅ Alert sent to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[notifier] ❌ Authentication failed.")
        print("           → Make sure you are using a Gmail APP PASSWORD, not your login password.")
        print("           → Generate one at: https://myaccount.google.com/apppasswords")
        return False

    except smtplib.SMTPException as e:
        print(f"[notifier] ❌ SMTP error: {e}")
        return False

    except Exception:
        print("[notifier] ❌ Unexpected error:")
        traceback.print_exc()
        return False