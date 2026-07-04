"""
backend/report.py
Generates a professional PDF incident report using reportlab.
The report content adapts based on the detected incident type.

Install: pip install reportlab
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

_SEV_COLOR = {
    "Low":      colors.HexColor("#22c55e"),
    "Medium":   colors.HexColor("#f59e0b"),
    "High":     colors.HexColor("#ef4444"),
    "Critical": colors.HexColor("#7c3aed"),
}
_SEV_LIGHT = {
    "Low":      colors.HexColor("#dcfce7"),
    "Medium":   colors.HexColor("#fef9c3"),
    "High":     colors.HexColor("#fee2e2"),
    "Critical": colors.HexColor("#f3e8ff"),
}

_INCIDENT_DB = {
    "fire": {
        "title": "Fire Incident Report",
        "description": (
            "A fire incident has been detected at the reported location. "
            "Immediate evacuation and fire suppression measures are required. "
            "The affected area must be cordoned off until declared safe by officials."
        ),
        "immediate_actions": [
            "Call Fire Department immediately — Helpline: 101",
            "Evacuate all personnel and civilians from the affected area",
            "Do NOT use water on electrical or chemical fires",
            "Use sand or CO2 fire extinguisher if safe to do so",
            "Alert nearest hospital for potential burn/smoke inhalation victims",
            "Shut off gas and electrical supply to the building if possible",
        ],
        "authority": "Fire Brigade: 101  |  Emergency: 112",
        "follow_up": [
            "File official fire incident report with the Fire Department",
            "Conduct structural safety inspection before re-entry",
            "Preserve evidence for insurance and forensic investigation",
            "Arrange counselling and support for affected residents",
        ],
    },
    "accident": {
        "title": "Road Accident Incident Report",
        "description": (
            "A road traffic accident has been detected at the reported location. "
            "Emergency medical services and traffic management are required immediately. "
            "The scene must be secured to prevent secondary accidents."
        ),
        "immediate_actions": [
            "Call Ambulance immediately — Helpline: 108",
            "Call Police to manage traffic and register FIR — Helpline: 100",
            "Do NOT move injured persons unless there is immediate danger",
            "Keep the scene clear for emergency vehicle access",
            "Provide basic first aid if trained to do so",
            "Turn on hazard lights and set up warning triangles if available",
        ],
        "authority": "Police: 100  |  Ambulance: 108  |  Emergency: 112",
        "follow_up": [
            "File FIR and Motor Accident Report (MAR) with police",
            "Notify insurance companies and relevant transport authorities",
            "Arrange for vehicle towing and road clearance",
            "Inspect and repair road damage if it contributed to the accident",
        ],
    },
    "flood": {
        "title": "Flood / Waterlogging Incident Report",
        "description": (
            "Flood or severe waterlogging has been detected at the reported location. "
            "This poses serious risk to life, infrastructure, and property. "
            "Immediate evacuation and activation of disaster response teams is required."
        ),
        "immediate_actions": [
            "Alert NDRF and local Disaster Management Authority",
            "Evacuate residents from low-lying and flood-prone areas",
            "Turn off electrical mains in affected areas to prevent electrocution",
            "Move to higher ground — avoid walking or driving through floodwater",
            "Open emergency shelters and arrange relief supplies",
            "Deploy boats and rescue teams for stranded individuals",
        ],
        "authority": "NDRF: 011-24363260  |  Emergency: 112",
        "follow_up": [
            "Assess structural damage to buildings and roads",
            "Conduct water quality testing before resuming supply",
            "Provide medical support for waterborne disease prevention",
            "Submit disaster damage report to state or central government",
        ],
    },
    "fight": {
        "title": "Public Disturbance / Violent Incident Report",
        "description": (
            "A public disturbance or violent altercation has been detected. "
            "Law enforcement response is required to restore order and protect bystanders."
        ),
        "immediate_actions": [
            "Call Police immediately — Helpline: 100",
            "Do NOT physically intervene",
            "Keep a safe distance and guide bystanders away",
            "Alert nearby security personnel or guards",
            "Document the incident if it is safe to do so",
            "Call ambulance if anyone is injured — Helpline: 108",
        ],
        "authority": "Police: 100  |  Ambulance: 108  |  Emergency: 112",
        "follow_up": [
            "File complaint and witness statements with police",
            "Review CCTV footage for evidence collection",
            "Provide support and counselling to victims",
            "Increase security patrol in the area",
        ],
    },
    "pothole": {
        "title": "Road Damage / Pothole Incident Report",
        "description": (
            "Significant road damage or a pothole has been detected. "
            "This poses a hazard to vehicles and pedestrians and requires prompt "
            "attention from the roads authority."
        ),
        "immediate_actions": [
            "Place warning signs or traffic cones around the pothole",
            "Alert local traffic police to manage vehicle flow",
            "Report to Municipal Corporation / PWD — Helpline: 1533",
            "Avoid heavy vehicle traffic over the damaged section",
            "Document with photographs for official records",
        ],
        "authority": "Municipal Helpline: 1533  |  PWD Department",
        "follow_up": [
            "Schedule emergency road repair within 24 to 48 hours",
            "File maintenance request on city portal",
            "Inspect surrounding road section for additional damage",
            "Update road condition records",
        ],
    },
    "garbage": {
        "title": "Illegal Dumping / Garbage Incident Report",
        "description": (
            "Illegal garbage dumping or an unsanitary condition has been detected. "
            "This is a public health hazard requiring immediate attention from "
            "sanitation authorities."
        ),
        "immediate_actions": [
            "Report to Municipal Sanitation Department — Helpline: 1969",
            "Cordon off the area if waste is hazardous",
            "Avoid direct contact with the waste material",
            "File complaint on Swachh Bharat app or citizen portal",
            "Alert public health department if medical waste is involved",
        ],
        "authority": "Sanitation Helpline: 1969  |  Swachh Bharat App",
        "follow_up": [
            "Schedule waste removal and area clean-up",
            "Identify and penalise the responsible party if possible",
            "Install CCTV or signage to deter future dumping",
            "Submit sanitation compliance report",
        ],
    },
}

_DEFAULT_INCIDENT = {
    "title": "General Incident Report",
    "description": (
        "An incident has been detected at the reported location by the Smart City "
        "AI monitoring system. Authorities are advised to assess the situation and "
        "take appropriate action based on the nature and severity of the incident."
    ),
    "immediate_actions": [
        "Contact local authorities and emergency services (112)",
        "Ensure public safety in the surrounding area",
        "Prevent unauthorised access to the incident site",
        "Document the incident for official reporting",
        "Deploy appropriate response teams as needed",
    ],
    "authority": "Emergency Services: 112",
    "follow_up": [
        "Complete official incident report and submit to relevant department",
        "Review AI detection logs for accuracy",
        "Arrange follow-up inspection of the site",
    ],
}


def _get_incident_info(incident_type: str) -> dict:
    lower = incident_type.lower()
    for key, val in _INCIDENT_DB.items():
        if key in lower:
            return val
    return _DEFAULT_INCIDENT


def _styles():
    s = {}
    s["title"] = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold",
                                textColor=colors.HexColor("#0f172a"),
                                alignment=TA_CENTER, spaceAfter=4)
    s["subtitle"] = ParagraphStyle("subtitle", fontSize=10, fontName="Helvetica",
                                   textColor=colors.HexColor("#64748b"),
                                   alignment=TA_CENTER, spaceAfter=2)
    s["section"] = ParagraphStyle("section", fontSize=11, fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#1e293b"),
                                  spaceBefore=12, spaceAfter=6)
    s["subsection"] = ParagraphStyle("subsection", fontSize=10, fontName="Helvetica-Bold",
                                     textColor=colors.HexColor("#374151"),
                                     spaceAfter=4, spaceBefore=8)
    s["body"] = ParagraphStyle("body", fontSize=9, fontName="Helvetica",
                               textColor=colors.HexColor("#374151"),
                               leading=14, spaceAfter=6)
    s["bullet"] = ParagraphStyle("bullet", fontSize=9, fontName="Helvetica",
                                 textColor=colors.HexColor("#374151"),
                                 leftIndent=12, leading=14, spaceAfter=3)
    s["footer"] = ParagraphStyle("footer", fontSize=7, fontName="Helvetica",
                                 textColor=colors.HexColor("#9ca3af"),
                                 alignment=TA_CENTER)
    return s


def generate_report(incident_type: str, severity: str, lat: float, lon: float,
                    nearby: dict = None) -> str:
    if nearby is None:
        nearby = {}

    info      = _get_incident_info(incident_type)
    sev_color = _SEV_COLOR.get(severity, colors.HexColor("#6b7280"))
    sev_light = _SEV_LIGHT.get(severity, colors.HexColor("#f3f4f6"))
    st        = _styles()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_id = datetime.now().strftime("SC-%Y%m%d-%H%M%S")
    maps_url  = f"https://www.google.com/maps?q={lat},{lon}"
    filename  = os.path.join(REPORTS_DIR, f"incident_{report_id}.pdf")

    doc = SimpleDocTemplate(filename, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    # ── Header banner ────────────────────────────────────────────────────────
    hdr = Table([[Paragraph(
        "<font color='white'><b>SMART CITY INCIDENT REPORT</b></font>",
        ParagraphStyle("h", fontSize=13, fontName="Helvetica-Bold",
                       textColor=colors.white, alignment=TA_CENTER)
    )]], colWidths=[17*cm])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#0f172a")),
        ("TOPPADDING",    (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 8))
    story.append(Paragraph(info["title"], st["title"]))
    story.append(Paragraph(f"Report ID: {report_id}  |  {timestamp}", st["subtitle"]))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 8))

    # ── Summary table ────────────────────────────────────────────────────────
    story.append(Paragraph("Incident Summary", st["section"]))
    rows = [
        ["Field", "Details"],
        ["Incident Type",  incident_type],
        ["Severity",       severity],
        ["Latitude",       f"{lat:.6f}"],
        ["Longitude",      f"{lon:.6f}"],
        ["Google Maps",    maps_url],
        ["Date & Time",    timestamp],
        ["Authority",      info["authority"]],
    ]
    t = Table(rows, colWidths=[5*cm, 12*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 8),
        ("BACKGROUND",     (0,1), (0,-1), colors.HexColor("#f8fafc")),
        ("FONTNAME",       (0,1), (0,-1), "Helvetica-Bold"),
        ("TEXTCOLOR",      (0,1), (0,-1), colors.HexColor("#475569")),
        ("BACKGROUND",     (1,2), (1,2), sev_light),
        ("TEXTCOLOR",      (1,2), (1,2), sev_color),
        ("FONTNAME",       (1,2), (1,2), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID",           (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # ── Description ──────────────────────────────────────────────────────────
    story.append(Paragraph("Incident Description", st["section"]))
    story.append(Paragraph(info["description"], st["body"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))

    # ── Immediate actions ────────────────────────────────────────────────────
    story.append(Paragraph("Recommended Immediate Actions", st["section"]))
    action_rows = [[Paragraph(f"  {chr(10004)}  {a}", st["bullet"])] for a in info["immediate_actions"]]
    a_table = Table(action_rows, colWidths=[16.5*cm])
    a_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), sev_light),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("LINEBEFORE",    (0,0), (0,-1), 3, sev_color),
    ]))
    story.append(a_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))

    # ── Nearby services ──────────────────────────────────────────────────────
    hospitals = nearby.get("hospitals", [])
    police    = nearby.get("police", [])

    if hospitals or police:
        story.append(Paragraph("Nearby Emergency Services", st["section"]))
        for label, places in [("Hospitals", hospitals), ("Police Stations", police)]:
            story.append(Paragraph(label, st["subsection"]))
            if places:
                svc_rows = [["Name", "Distance", "Coordinates"]]
                for p in places:
                    svc_rows.append([
                        p.get("name", "N/A"),
                        f"{p.get('distance_km', '?')} km",
                        f"{p.get('lat',0):.4f}, {p.get('lon',0):.4f}",
                    ])
                st2 = Table(svc_rows, colWidths=[8*cm, 3*cm, 6*cm])
                st2.setStyle(TableStyle([
                    ("BACKGROUND",     (0,0), (-1,0), colors.HexColor("#334155")),
                    ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
                    ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",       (0,0), (-1,-1), 8),
                    ("GRID",           (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("TOPPADDING",     (0,0), (-1,-1), 5),
                    ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
                    ("LEFTPADDING",    (0,0), (-1,-1), 8),
                ]))
                story.append(st2)
                story.append(Spacer(1, 6))
            else:
                story.append(Paragraph("None found within 3 km.", st["body"]))

        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))

    # ── Follow-up ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Follow-Up Actions Required", st["section"]))
    for action in info["follow_up"]:
        story.append(Paragraph(f"  {chr(8226)}  {action}", st["bullet"]))

    story.append(Spacer(1, 18))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Auto-generated by Smart City Incident Detection System on {timestamp}. "
        "For official use only. Verify all information before taking action.",
        st["footer"]
    ))

    doc.build(story)
    print(f"[report]   Report saved: {filename}")
    return filename