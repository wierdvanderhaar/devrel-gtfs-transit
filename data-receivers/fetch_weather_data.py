import requests
import json
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from dotenv import load_dotenv
from crate import client
import time

# Load environment variables
load_dotenv()
NOAA_API_TOKEN = os.getenv("NOAA_API_TOKEN")
CRATEDB_URL = os.getenv("CRATEDB_URL")

# NOAA & Weather API Configs
STATION_ID = "GHCND:USW00013743"
DATASET = "GHCND"
START_DATE = "2020-01-01"

CURRENT_WEATHER_URL = "https://api.weather.gov/stations/KDCA/observations/latest"
FORECAST_URL = "https://api.weather.gov/gridpoints/LWX/97,71/forecast"
WEATHER_STATION = "KDCA"

# Mapping NOAA abbreviations to readable names
ABBREVIATION_MAP = {
    "TMAX": "Max Temperature (°F)",
    "TMIN": "Min Temperature (°F)",
    "TAVG": "Average Temperature (°F)",
    "AWND": "Average Wind Speed (mph)",
    "WSF2": "Fastest Wind Speed (2 min avg, mph)",
    "WSF5": "Fastest Wind Speed (5 sec avg, mph)",
    "WDF2": "Wind Direction (2 min avg, degrees)",
    "WDF5": "Wind Direction (5 sec avg, degrees)",
    "PRCP": "Precipitation (mm)",
    "SNOW": "Snowfall (mm)",
    "SNWD": "Snow Depth (mm)",
    "RHAV": "Average Relative Humidity (%)",
    "RHMN": "Min Relative Humidity (%)",
    "RHMX": "Max Relative Humidity (%)",
    "ASLP": "Sea Level Pressure (Pa)",
    "ASTP": "Station Pressure (Pa)",
    "ADPT": "Dew Point (°F)",
    "AWBT": "Wet Bulb Temperature (°F)"
}

def get_latest_available_date():
    """Fetch the latest available date for the dataset"""
    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets"
    headers = {"token": NOAA_API_TOKEN}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch dataset info: {response.status_code}")
        return None
    
    datasets = response.json().get("results", [])
    for dataset in datasets:
        if dataset["id"] == "GHCND":
            return dataset["maxdate"]

    return None

def fetch_historical_weather_paginated():
    """Fetch historical weather data with pagination to get all records."""
    latest_date = get_latest_available_date()
    if not latest_date:
        print("⚠️ Could not determine latest available date.")
        return []
    
    start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_date = datetime.strptime(latest_date, "%Y-%m-%d")
    
    weather_data = []
    max_retries = 5
    records_per_request = 1000  # NOAA limit

    while start_date < end_date:
        next_end_date = start_date + timedelta(days=365)
        if next_end_date > end_date:
            next_end_date = end_date
        
        offset = 0  # Pagination start
        more_data = True

        while more_data:
            url = f"https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&stationid={STATION_ID}&startdate={start_date.strftime('%Y-%m-%d')}&enddate={next_end_date.strftime('%Y-%m-%d')}&limit={records_per_request}&offset={offset}"
            
            headers = {"token": NOAA_API_TOKEN}
            retries = 0
            success = False

            while retries < max_retries and not success:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json().get("results", [])
                    if data:
                        weather_data.extend(data)
                        offset += records_per_request  # Move to the next page
                    else:
                        more_data = False  # Stop pagination if no more data
                    success = True
                elif response.status_code == 503:
                    wait_time = 2 ** retries
                    print(f"⚠️ NOAA API unavailable (503). Retrying in {wait_time} sec...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    print(f"❌ Failed to fetch data for {start_date} - {next_end_date}: {response.status_code}")
                    more_data = False
                    break

        start_date = next_end_date + timedelta(days=1)

    return process_historical_data(weather_data)

def process_historical_data(data):
    """Process NOAA historical weather data into structured format."""
    weather_data = defaultdict(lambda: {"forecast": {}})

    for entry in data:
        date = entry["date"]
        station = entry["station"]
        datatype = entry["datatype"]
        value = entry["value"]

        transformed_name = ABBREVIATION_MAP.get(datatype, datatype)
        weather_data[date]["timestamp"] = date
        weather_data[date]["location"] = station
        weather_data[date]["forecast"][transformed_name] = value

    return list(weather_data.values())

def fetch_current_weather():
    """Fetch latest weather conditions from Weather.gov."""
    try:
        response = requests.get(CURRENT_WEATHER_URL, headers={"accept": "application/geo+json"})
        data = response.json()

        properties = data.get("properties", {})
        if not properties:
            return None

        forecast_data = {
            "forecast_date": datetime.now(timezone.utc).date().isoformat(),
            "Temperature (°F)": properties.get("temperature", {}).get("value"),
            "Dew Point (°F)": properties.get("dewpoint", {}).get("value"),
            "Relative Humidity (%)": properties.get("relativeHumidity", {}).get("value"),
            "Wind Speed (mph)": properties.get("windSpeed", {}).get("value"),
            "Wind Direction (°)": properties.get("windDirection", {}).get("value"),
            "Pressure (Pa)": properties.get("barometricPressure", {}).get("value"),
            "Precipitation (mm)": properties.get("precipitationLastHour", {}).get("value")
        }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": WEATHER_STATION,
            "forecast": {k: v for k, v in forecast_data.items() if v is not None}  # Remove nulls
        }

    except Exception as e:
        print(f"Error fetching current weather: {e}")
        return None

def fetch_forecast():
    """Fetch weather forecast for today and tomorrow from Weather.gov."""
    try:
        response = requests.get(FORECAST_URL, headers={"accept": "application/geo+json"})
        data = response.json()

        periods = data.get("properties", {}).get("periods", [])
        if not periods:
            return []

        forecast_entries = []
        today = datetime.now(timezone.utc).date()
        tomorrow = today + timedelta(days=1)

        for i, period in enumerate(periods[:2]):
            forecast_date = today if i == 0 else tomorrow

            forecast_data = {
                "forecast_date": forecast_date.isoformat(),
                "Temperature High (°F)": period.get("temperature") if period.get("isDaytime") else None,
                "Temperature Low (°F)": period.get("temperature") if not period.get("isDaytime") else None,
                "Wind Speed": period.get("windSpeed"),
                "Wind Direction": period.get("windDirection"),
                "Weather Description": period.get("shortForecast"),
                "Precipitation Chance (%)": period.get("probabilityOfPrecipitation", {}).get("value"),
            }

            forecast_entries.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": WEATHER_STATION,
                "forecast": {k: v for k, v in forecast_data.items() if v is not None}  # Remove nulls
            })

        return forecast_entries

    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return []

def insert_into_db(table, data):
    """Insert data into CrateDB."""
    if not data:
        return

    conn = client.connect(CRATEDB_URL)
    cursor = conn.cursor()

    for record in data:
        cursor.execute(f"INSERT INTO doc.{table} (timestamp, location, forecast) VALUES (?, ?, ?)", 
                       (record["timestamp"], record["location"], json.dumps(record["forecast"])))

    cursor.close()

# Run
insert_into_db("weather_data", fetch_historical_weather_paginated())
insert_into_db("weather_forecast", fetch_forecast())
insert_into_db("weather_forecast", [fetch_current_weather()])