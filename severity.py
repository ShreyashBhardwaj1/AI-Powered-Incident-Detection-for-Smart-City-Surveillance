def calculate_severity(incident_type):
    if incident_type == "Fire":
        return "High"
    elif incident_type == "Accident":
        return "Medium"
    elif incident_type == "Violence":
        return "High"
    else:
        return "Low"