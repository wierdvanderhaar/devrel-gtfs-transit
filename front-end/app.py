import json
import os
from crate import client
from dotenv import load_dotenv
from flask import Flask, render_template

# Load environment variables / secrets from .env file.
load_dotenv()

app = Flask(__name__)

# Connect to CrateDB
conn = client.connect(os.environ["CRATEDB_URL"])

@app.route("/api/networkmap")
def get_network_map():
    agency_name = os.environ["GTFS_AGENCY_NAME"]
    results = { "results": [] }

    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT network FROM network WHERE agency_name = '{agency_name}'")
        res = cursor.fetchone()
        results["results"].append(json.loads(res[0]))
    finally:
        cursor.close()

    return results

@app.route("/api/routeinfo")
def get_route_colors():
    agency_id = os.environ["GTFS_AGENCY_ID"]
    results = { "results": [] }

    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT route_id, route_short_name, route_long_name, route_color, route_text_color FROM route WHERE agency_id='{agency_id}'")
        
        for route in cursor.fetchall():
            result = {
                "id": route[0],
                "shortName": route[1],
                "longName": route[2],
                "color": f"#{route[3]}",
                "textColor": f"#{route[4]}"
            }

            results["results"].append(result)
    finally:
        cursor.close()

    return results

@app.route("/api/vehiclepositions")
def get_vehicle_positions():
    agency_id = os.environ["GTFS_AGENCY_ID"]
    results = { "results": [] }

    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT timestamp, vehicle['trip']['trip_id'], vehicle['vehicle']['label'], vehicle['trip']['route_id'], vehicle['position']['position'] FROM vehicle_positions WHERE agency_id = '{agency_id}' AND timestamp = (SELECT max(timestamp) FROM vehicle_positions WHERE agency_id = '{agency_id}')")

        for vehicle in cursor.fetchall():
            result = {
                "timestamp": vehicle[0],
                "tripId": vehicle[1],
                "vehicleId": vehicle[2],
                "line": vehicle[3],
                "latitude": vehicle[4][0],
                "longitude": vehicle[4][1]
            }

            results["results"].append(result)

    finally:
        cursor.close()
    
    return results

# TODO add a route for the front end to get its configuration...
# Initial lat, long
# Initial zoom, max zoom
# Agency name e.g. WMATA

@app.route("/api/config")
def get_config():
    # TODO pass in an agency name?
    return "TODO"

@app.route("/")
def homepage():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(port=8000) # TODO move to environment variables.