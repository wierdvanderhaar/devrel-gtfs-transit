import csv
import json
import sys
from crate import client
from dotenv import load_dotenv

# Load environment variables / secrets from .env file.
load_dotenv()

# TODO this needs a plural name
# CREATE TABLE IF NOT EXISTS agency (
#     agency_id TEXT PRIMARY KEY,
#     agency_name TEXT,
#     agency_url TEXT,
#     agency_timezone TEXT,
#     agency_lang TEXT,
#     agency_phone TEXT,    
#     agency_fare_url TEXT
# );

# TODO this needs a plural name
# TODO add agency id to this somehow
# CREATE TABLE IF NOT EXISTS network (
#     agency_name TEXT PRIMARY KEY,
#     network TEXT INDEX OFF STORAGE WITH (columnstore = false)
# );

# TODO this needs a plural name
# CREATE TABLE IF NOT EXISTS route (
#     route_id TEXT,
#     agency_id TEXT,
#     route_short_name TEXT,
#     route_long_name TEXT,
#     route_desc TEXT,
#     route_type TEXT,
#     route_url TEXT,
#     route_color TEXT,
#     as_route TEXT,
#     network_id TEXT,
#     route_text_color TEXT
# );

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


def load_agency_data(file_name):
    header_row, data_rows = load_csv_file(file_name)
    insert_data("agency", header_row, data_rows)
    print("Inserted agency data.")


def load_route_data(file_name):
    header_row, data_rows = load_csv_file(file_name)
    insert_data("route", header_row, data_rows)
    print("Inserted route data.") 
    

def load_network_data(file_name):
    agency_name = "WeGo Public Transit" # TODO read this from a file.

    with open(file_name) as geojson_file:
        geojson = json.load(geojson_file)
    
    print(json.dumps(geojson))

    conn = client.connect(os.environ["CRATEDB_URL"])
    cursor = conn.cursor() 

    try:
        cursor.execute(
            "INSERT INTO network (agency_name, network) VALUES (?, ?)",
            (agency_name, json.dumps(geojson))
        )
    finally:
        cursor.close()

    print("Inserted network data.")

if len(sys.argv) != 2:
    print("You need to pass in a file name!")
elif sys.argv[1].endswith("agency.txt"):
    load_agency_data(sys.argv[1])
elif sys.argv[1].endswith("routes.txt"):
    load_route_data(sys.argv[1])
elif sys.argv[1].endswith(".geojson"):
    load_network_data(sys.argv[1])
else:
    print("Not a recognized file name.")
