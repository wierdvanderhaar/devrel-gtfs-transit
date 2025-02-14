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
