import csv
import json
import os
import sys
from crate import client
from dotenv import load_dotenv

# Load environment variables / secrets from .env file.
load_dotenv()

def create_tables():
    conn = client.connect(os.environ["CRATEDB_URL"])
    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agencies (
                agency_id TEXT,
                agency_name TEXT PRIMARY KEY,
                agency_url TEXT,
                agency_timezone TEXT,
                agency_lang TEXT,
                agency_phone TEXT,    
                agency_fare_url TEXT
            )
        """)

        print("Created agencies table if needed.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS networks (
                agency_name TEXT PRIMARY KEY,
                agency_id TEXT,
                network TEXT INDEX OFF STORAGE WITH (columnstore = false)
            )
        """)

        print("Created networks table if needed.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stations (
            "stop_id" TEXT NOT NULL,
            "stop_name" TEXT,
            "latitude" DOUBLE PRECISION,
            "longitude" DOUBLE PRECISION,
            "line" TEXT,
            PRIMARY KEY ("stop_id")
            )
        """)

        print("Created stations table if needed.")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                route_id TEXT,
                agency_id TEXT,
                route_short_name TEXT,
                route_long_name TEXT,
                route_desc TEXT,
                route_type TEXT,
                route_url TEXT,
                route_color TEXT,
                as_route TEXT,
                network_id TEXT,
                route_text_color TEXT
            )
        """)

        print("Created routes table if needed.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_positions (
                id TEXT,
                agency_id TEXT,
                timestamp TIMESTAMP,
                vehicle OBJECT(DYNAMIC)
            )
        """)

        print("Created vehicle positions table if needed.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trip_updates (
                id TEXT,
                agency_id TEXT,
                timestamp TIMESTAMP,
                details OBJECT(DYNAMIC)
            )
        """)

        print("Created trip updates table if needed.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                agency_id TEXT PRIMARY KEY,
                configuration OBJECT(DYNAMIC)
            )
        """)

        print("Created config table if needed.")

        print("Finished creating any necessary tables.")
    finally:
        cursor.close()

def load_csv_file(file_name):
    first_row = True

    with open(file_name, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar='"')
        header_row = None
        data_rows = []

        for row in reader:
            if (first_row):
                first_row = False
                header_row = row
            else:
                data_rows.append(tuple(row))

    return (header_row, data_rows)


def insert_data(table_name, column_names, rows):
    conn = client.connect(os.environ["CRATEDB_URL"])
    cursor = conn.cursor()

    try:
        cursor.executemany(
            f"INSERT INTO {table_name} ({','.join([str(s) for s in column_names])}) VALUES ({','.join(['?'] * len(column_names))})", 
            rows
        )
    finally:
        cursor.close()

def load_config_data(file_name):
    with open(file_name) as config_file:
        conf = json.load(config_file)

    conn = client.connect(os.environ["CRATEDB_URL"])
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO config (agency_id, configuration) VALUES (?, ?)",
            (conf["agencyId"], json.dumps(conf["configuration"]))
        )
    finally:
        cursor.close()

    print("Inserted config data.")
    

def load_agency_data(file_name):
    header_row, data_rows = load_csv_file(file_name)
    insert_data("agencies", header_row, data_rows)
    print("Inserted agency data.")


def load_route_data(file_name):
    header_row, data_rows = load_csv_file(file_name)
    insert_data("routes", header_row, data_rows)
    print("Inserted route data.") 
    

def load_network_data(file_name, agency_name):
    with open(file_name) as geojson_file:
        geojson = json.load(geojson_file)

    conn = client.connect(os.environ["CRATEDB_URL"])
    cursor = conn.cursor()

    station_data = []

    # ✅ Extract station data from "features"
    for feature in geojson.get("features", []):  # Check for "features" instead of "stations"
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        stop_id = properties.get("stop_id")
        stop_name = properties.get("stop_name", "Unknown")
        lat = geometry.get("coordinates", [None, None])[1]  # Lat is second in [lon, lat]
        lon = geometry.get("coordinates", [None, None])[0]  # Lon is first

        # Extract the first route (if available)
        routes = properties.get("routes", [])
        route_info = routes[0] if routes else {}  # Get the first route
        line = route_info.get("route_short_name", "Unknown")

        if stop_id:
            station_data.append((stop_id, stop_name, lat, lon, line))

    try:
        # ✅ Insert full network JSON
        cursor.execute(
            "INSERT INTO networks (agency_name, network) VALUES (?, ?) ON CONFLICT (agency_name) DO UPDATE SET network = EXCLUDED.network",
            (agency_name, json.dumps(geojson))
        )
        print("✅ Inserted network data.")

        # ✅ Only insert stations if there is data
        if station_data:
            cursor.executemany(
                "INSERT INTO stations (stop_id, stop_name, latitude, longitude, line) VALUES (?, ?, ?, ?, ?) ON CONFLICT (stop_id) DO NOTHING",
                station_data
            )
            print(f"✅ Inserted {len(station_data)} stations into CrateDB.")
        else:
            print("⚠️ No station data found in geojson!")

    finally:
        cursor.close()

if len(sys.argv) < 2:
    print("You need to pass in a file name and/or other parameters!")
elif len(sys.argv) == 2 and sys.argv[1] == "createtables":
    create_tables()
elif len(sys.argv) == 2 and sys.argv[1].endswith("agency.txt"):
    load_agency_data(sys.argv[1])
elif len(sys.argv) == 2 and sys.argv[1].endswith("routes.txt"):
    load_route_data(sys.argv[1])
elif len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
    load_config_data(sys.argv[1])
elif len(sys.argv) == 3 and sys.argv[1].endswith(".geojson"):
    load_network_data(sys.argv[1], sys.argv[2])
else:
    print("Invalid usage.")
