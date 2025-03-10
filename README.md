# TODO Title

## Introduction

TODO

## Prerequisites

TODO

## Getting the Code

Next you'll need to get a copy of the code from GitHub by cloning the repository. Open up your terminal and change directory to wherever you store coding projects, then enter the following commands:

git clone https://github.com/crate/devrel-gtfs-transit.git
cd devrel-gtfs-transit

## Getting a CrateDB Database

TODO

## Creating the Database Tables

We've provided a Python data loader script that will create the database tables in CrateDB for you.

You'll first need to create a virtual environment for the data loader and configure it:

```bash
cd gtfs-static
python -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

Now make a copy of the example environment file provided:

```bash
cp env.example .env
```

Edit the `.env` file, changing the value of `CRATEDB_URL` to be the connection URL for your CrateDB database.

If you're running CrateDB locally (for example with the provided Docker Compose file) there's nothing to change here.

If you're running CrateDB in the cloud, change the connection URL as follows, using the values for your cloud cluster instance:

```
https://admin:<password>@<hostname>:4200
```

Save your changes.

Next, run the data loader to create the tables used by this project:

```bash
python dataloader.py createtables
```

You should see output similar to this:

```
Created agencies table if needed.
Created networks table if needed.
Created routes table if needed.
Created vehicle positions table if needed.
Created config table if needed.
Finished creating any necessary tables.
```

Use the CrateDB console to verify that tables named `agencies`, `config`, `networks`, `routes` and `vehicle_positions` were created in the `doc` schema.

## Load the Static Data

The next step is to load static data about the transport network into the database.  We'll use Washington DC (WMATA) as an example. 

First, load the configuration data for the agency:

```bash
python dataloader.py config-files/wmata.json
```

Now, load data into the `agencies` table:

```bash
python dataloader.py data-files/wmata/agency.txt
```

Next, populate the `routes` table:

```bash
python dataloader.py data-files/wmata/routes.txt
```

Finally, insert data into the `networks` table.  Here `WMATA` is the agency name, and must match the spelling and capitalization of the agency name in `agency.txt`:

```bash
python dataloader.py geojson/wmata/wmata.geojson WMATA
```

## Start the Front End Flask Application

TODO description.

Before starting the front end Flask application, you'll need to create a virtual environment and configure it:

```bash
cd front-end
python -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

Now make a copy of the example environment file provided:

```bash
cp env.example .env
```

Edit the `.env` file, changing the value of `CRATEDB_URL` to be the connection URL for your CrateDB database.

If you're running CrateDB locally (for example with the provided Docker Compose file) there's nothing to change here.

If you're running CrateDB in the cloud, change the connection URL as follows, using the values for your cloud cluster instance:

```
https://admin:<password>@<hostname>:4200
```

Now, edit the values of `GTFS_AGENCY_NAME` and `GTFS_AGENCY_ID` to contain the agency name and ID for the agency you're using.  These should match the values returned by this query:

```sql
SELECT agency_name, agency_id FROM agencies
```

For example, for Washington DC / WMATA, the correct settings are:

```
GTFS_AGENCY_NAME=WMATA
GTFS_AGENCY_ID=1
```

Don't forget that if either value contains a space, you'll need to surround the entire value with quotation marks.

Save your changes.

Now, start the front end application:

```bash
python app.py
```

Using your browser, visit `http://localhost:8000` to view the map front end interface.  

At this point you should see the route map for the agency that you're working with, along with the stations / stops on the routes.  Clicking a station or stop should show information about it.

No vehicles will be visible on the map yet.  To see these, you'll need to run the real time data receiver components (see below).  

## Start the Real Time Data Receiver Components

The real time data receiver components are responsible for reading real time vehicle location and other data from the transit agencies and saving it in the database.

First, create a virtual environment and install the dependencies:

```bash
cd front-end
python -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

Now make a copy of the example environment file provided:

```bash
cp env.example .env
```

dit the `.env` file, changing the value of `CRATEDB_URL` to be the connection URL for your CrateDB database.

If you're running CrateDB locally (for example with the provided Docker Compose file) there's nothing to change here.

If you're running CrateDB in the cloud, change the connection URL as follows, using the values for your cloud cluster instance:

```
https://admin:<password>@<hostname>:4200
```

Now, edit the value of `GTFS_AGENCY_ID` to contain the ID for the agency you're using.  It should match the value returned by this query:

```sql
SELECT agency_id FROM agencies
```

For example, for Washington DC / WMATA, the correct setting is:

```
GTFS_AGENCY_ID=1
```

Set the value of `SLEEP_INTERVAL` to be the number of seconds that the component sleeps between checking the transit agency for updates.  This defaults to `1`, but you may need to set a longer interval if the agency you're using implements rate limiting on its API endpoints.

Next, set the value of `GTFS_POSITIONS_FEED_URL` to the realtime vehicle movements endpoint URL for your agency.  For example for Washington DC / WMATA this is `https://api.wmata.com/gtfs/rail-gtfsrt-vehiclepositions.pb`.

Finally, if your agency requires an API key to access realtime vehicle movements data, set the value of `GTFS_POSITIONS_FEED_KEY` appropriately.

Save your changes.

Start gathering real time vehicle position data by running this command:

```bash
python realtime.py
```

Assuming that the Flask front end web application is running, you should now see vehicle movement details at `http://localhost:8000`.

## Work in Progress Notes Below

Getting GeoJSON from GTFS:

https://github.com/BlinkTagInc/gtfs-to-geojson

```bash
cd gtfs-static
gtfs-to-geojson --configPath ./config_wego.json
```

Getting GTFS static data for WMATA rail:

```bash
wget --header="api_key: <REDACTED>" https://api.wmata.com/gtfs/rail-gtfs-static.zip
```

List of many GTFS feeds:

https://gist.githubusercontent.com/AvidDabbler/b3e8fc4afccfb8b371ae8638e7ff0ba6/raw/eec0665f26483dd9652a34114e944a65b94650af/gtfs-feeds.json

WMATA Information

* https://developer.wmata.com/api-details#api=gtfs&operation=5cdc5367acb52c9350f69753

Nashville Information

This is an automated email from IIS7 - Nashville MTA GIS and Real-Time GTFS Data

This data is available at the following URLs:

GTFS DATA: https://www.nashvillemta.org/GoogleExport/google_transit.zip

ROUTE DATA: https://www.nashvillemta.org/GoogleExport/google_routes.zip

STOP DATA: https://www.nashvillemta.org/GoogleExport/google_stops.zip

Service Alerts:
http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/alert/alerts.pb

Trip Updates:
http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/tripupdate/tripupdates.pb

Vehicle Positions:
http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/vehicle/vehiclepositions.pb

http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/gtfs-realtime/trapezerealtimefeed.pb

Swiss GTFS RT Portal

https://opentransportdata.swiss/en/cookbook/gtfs-rt/