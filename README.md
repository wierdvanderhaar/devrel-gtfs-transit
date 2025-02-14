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

Nashville MTA
Real-Time GTFS Transit Data API

Developers should referance Google Transit API for more information: https://developers.google.com/transit/

Service Alerts:
http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/alert/alerts.pb

Trip Updates:
http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/tripupdate/tripupdates.pb

Vehicle Positions:
http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/vehicle/vehiclepositions.pb

http://transitdata.nashvillemta.org/TMGTFSRealTimeWebService/gtfs-realtime/trapezerealtimefeed.pb
