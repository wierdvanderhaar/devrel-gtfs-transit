from crate import client
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
from google.protobuf.message import DecodeError
from time import sleep
import os
import requests

# Load environment variables / secrets from .env file.
load_dotenv()

SLEEP_INTERVAL = int(os.environ["SLEEP_INTERVAL"])

def update_trips():
    agency_id = os.environ["GTFS_AGENCY_ID"]

    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(
        os.environ["GTFS_TRIPS_FEED_URL"],
        headers = {
            "Cache-Control": "no-cache",
            "api_key": os.environ["GTFS_TRIPS_FEED_KEY"] # TODO make auth mechanism an env var
        }
    )

    try:
        feed.ParseFromString(response.content)
        entities = protobuf_to_dict(feed)
    except DecodeError as ex:
        print(f"{agency_id}: Error decoding message:")
        print(ex)
        return
    
    feed_ts = entities["header"]["timestamp"]

    conn = client.connect(os.environ["CRATEDB_URL"])
    trip_update_data = []
    cursor = conn.cursor()

    cursor.execute(f"SELECT max(timestamp) FROM trip_updates WHERE agency_id='{agency_id}'")
    res = cursor.fetchone()
    latest_in_db = 0 if res[0] is None else res[0] 

    print(f"{agency_id}: timestamp from feed: {entities["header"]["timestamp"]}, latest in db: {latest_in_db}")

    if feed_ts <= latest_in_db:
        print(f"{agency_id}: Nothing new to store this time.")
        return

    for entity in entities["entity"]:
        # TODO remove any fields we don't need?

        trip_update_data.append((
            f"{entity["id"]}-{entity["trip_update"]["timestamp"]}",
            agency_id,
            feed_ts,
            entity["trip_update"]
        ))

    # TODO save it in the database...
    print(trip_update_data)

    # https://cratedb.com/docs/python/en/latest/query.html#bulk-inserts
    result = cursor.executemany(
        "INSERT INTO trip_updates (id, agency_id, timestamp, details) VALUES (?, ?, ?, ?)",
        trip_update_data
    )

    print(f"{agency_id}: Processed {len(entities["entity"])} trip updates.")

    cursor.close()


while True:
    update_trips()
    sleep(SLEEP_INTERVAL)