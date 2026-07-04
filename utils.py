import json, math

def distance(a, b, c, d):
    return math.sqrt((a-c)**2 + (b-d)**2)

def find_nearest(lat, lon, path):

    with open(path) as f:
        data = json.load(f)

    nearest = min(data, key=lambda x:
        distance(lat, lon, x["lat"], x["lon"])
    )

    return nearest