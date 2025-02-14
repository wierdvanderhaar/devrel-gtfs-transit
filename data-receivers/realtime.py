from crate import client
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
from time import sleep
import json
import requests


# TODO some stuff with loading environment variables.

def update_vehicle_positions():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(
        'https://api.wmata.com/gtfs/rail-gtfsrt-vehiclepositions.pb',
        headers = {
            'Cache-Control': 'no-cache',
            'api_key': '<redcated>' # TODO move to environment variables.
        }
    )

    feed.ParseFromString(response.content)
    entities = protobuf_to_dict(feed)

    # create table vehicle_positions (
    #   id text primary key,
    #   sequence bigint,
    #   timestamp timestamp,
    #   vehicle object(dynamic)
    # );

    conn = client.connect("http://localhost:4200/", username="crate") # TODO consolidated into just URL and use env vars
    vehicle_position_data = []

    cursor = conn.cursor()

    cursor.execute("SELECT max(timestamp) FROM vehicle_positions")
    res = cursor.fetchone()
    feed_ts = entities["header"]["timestamp"]
    latest_in_db = res[0]

    print(f"timestamp from feed: {entities["header"]["timestamp"]}, latest in db: {latest_in_db}")

    if feed_ts <= latest_in_db:
        print("Nothing new to store this time.")
        return

    for entity in entities["entity"]:
        if entity["is_deleted"] == True:
            continue

        del entity["is_deleted"]
        entity["vehicle"]["position"]["position"] = [ entity["vehicle"]["position"]["longitude"], entity["vehicle"]["position"]["latitude"] ]
        timestamp = entity["vehicle"]["timestamp"]
        del entity["vehicle"]["timestamp"]

        vehicle_position_data.append((
            f"""{entity["vehicle"]["trip"]["trip_id"]}-{timestamp}""",
            int(entity["id"]),
            timestamp,
            entity["vehicle"]
        ))

    # https://cratedb.com/docs/python/en/latest/query.html#bulk-inserts
    result = cursor.executemany(
        "INSERT INTO vehicle_positions (id, sequence, timestamp, vehicle) VALUES (?, ?, ?, ?)",
        vehicle_position_data
    )

    print(f"Updated {len(entities["entity"])} vehicle positions.")

while True:
    update_vehicle_positions()
    sleep(1) # TODO make this configurable in env var.