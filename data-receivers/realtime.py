from crate import client
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
from time import sleep
import json
import os
import requests

# Load environment variables / secrets from .env file.
load_dotenv()

SLEEP_INTERVAL = int(os.environ["SLEEP_INTERVAL"])

def update_vehicle_positions():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(
        os.environ["GTFS_FEED_URL"],
        headers = {
            "Cache-Control": "no-cache",
            "api_key": os.environ["GTFS_FEED_KEY"] # TODO make auth mechanism an env var
        }
    )

    feed.ParseFromString(response.content)
    entities = protobuf_to_dict(feed)

    # create table vehicle_positions (
    #   id text,
    #   agency_id text,
    #   timestamp timestamp,
    #   vehicle object(dynamic)
    # );

    conn = client.connect(os.environ["CRATEDB_URL"])
    vehicle_position_data = []

    cursor = conn.cursor()

    agency_id = os.environ["GTFS_AGENCY_ID"]
    cursor.execute(f"SELECT max(timestamp) FROM vehicle_positions WHERE agency_id='{agency_id}'")
    res = cursor.fetchone()

    feed_ts = entities["header"]["timestamp"]
    latest_in_db = 0 if res[0] is None else res[0] 

    print(f"timestamp from feed: {entities["header"]["timestamp"]}, latest in db: {latest_in_db}")

    if feed_ts <= latest_in_db:
        print("Nothing new to store this time.")
        return

    for entity in entities["entity"]:
        print(entity)
        # Ignore entries that might be marked as logically deleted.
        if "is_deleted" in entity and entity["is_deleted"] == True:
            continue

        # Tidy up if needed.
        if "is_deleted" in entity:
            del entity["is_deleted"]

        entity["vehicle"]["position"]["position"] = [ entity["vehicle"]["position"]["longitude"], entity["vehicle"]["position"]["latitude"] ]
        timestamp = entity["vehicle"]["timestamp"]
        del entity["vehicle"]["timestamp"]

        vehicle_position_data.append((
            #f"""{entity["vehicle"]["trip"]["trip_id"]}-{timestamp}""",
            f"""{entity["id"]}-{timestamp}""",
            agency_id,
            timestamp,
            entity["vehicle"]
        ))

    # https://cratedb.com/docs/python/en/latest/query.html#bulk-inserts
    result = cursor.executemany(
        # TODO get agency name from env vars.
        "INSERT INTO vehicle_positions (id, agency_id, timestamp, vehicle) VALUES (?, ?, ?, ?)",
        vehicle_position_data
    )

    print(f"{agency_id}: Updated {len(entities["entity"])} vehicle positions.")

while True:
    update_vehicle_positions()
    sleep(SLEEP_INTERVAL) # TODO make this configurable in env var.