import streamlit as st
import requests
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Weather App", page_icon="☀️")

# WMO Weather Codes
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}

def get_WMO(code):
    return WMO_CODES.get(code, "Unknown weather condition")

def wind_direction(degree):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((degree / 45) % 8)
    return directions[idx]

# API Calls
def geocode(city):
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 5, "language": "en", "format": "json"},
        timeout=8,
    )
    r.raise_for_status()
    return r.json().get("results", [])

def fetch_weather(lat, lon):
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation,weathercode,uv_index",
            "hourly": "temperature_2m,precipitation_probability",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "auto",
            "forecast_days": 7,
        },
        timeout=8,
    )
    r.raise_for_status()
    return r.json()

# UI
st.title("☀️ Weather App Dashboard")
st.caption("Get the current weather and 7-day forecast for any city in the world.")

city_input = st.text_input("Enter a city name", placeholder="e.g. London, Paris, New York")
unit = st.radio("Select temperature unit", ("Celsius", "Fahrenheit"), horizontal=True)

if not city_input:
    st.info("Please enter a city name to get the weather information.")
    st.stop()

# Get location
with st.spinner("Fetching location data..."):
    try:
        locations = geocode(city_input)
    except Exception as e:
        st.error(f"Geocode Failed: {e}")
        st.stop()

if not locations:
    st.warning("No locations found. Please check the city name and try again.")
    st.stop()

# Select location
if len(locations) == 1:
    loc = locations[0]
else:
    options = [f"{r['name']}, {r.get('admin1','')}, {r['country']}" for r in locations]
    chosen_ind = st.selectbox("Select the correct location", range(len(options)),
                              format_func=lambda x: options[x])
    loc = locations[chosen_ind]

# Fetch weather
with st.spinner("Fetching weather data..."):
    try:
        data = fetch_weather(loc["latitude"], loc["longitude"])
    except Exception as e:
        st.error(f"Weather Fetch Failed: {e}")
        st.stop()

cur = data["current"]
daily = data["daily"]
hourly = data["hourly"]

# Unit conversion
def fmt(c):
    return round(c * 9 / 5 + 32, 1) if unit == "Fahrenheit" else c

unit_symbol = "°C" if unit == "Celsius" else "°F"

# Current Weather
st.divider()
st.subheader("Current Weather")

desc = get_WMO(cur["weathercode"])

st.metric(
    "Temperature",
    f"{fmt(cur['temperature_2m'])}{unit_symbol}",
    f"Feels like {fmt(cur['apparent_temperature'])}{unit_symbol}"
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("💧 Humidity", f"{cur['relative_humidity_2m']}%")
col2.metric("🌬 Wind", f"{cur['wind_speed_10m']} km/h {wind_direction(cur['wind_direction_10m'])}")
col3.metric("🌧 Precipitation", f"{cur['precipitation']} mm")
col4.metric("🌞 UV Index", f"{cur['uv_index']}")

st.caption(f"Condition: {desc}")

# Hourly Temperature Chart
st.subheader("Hourly Temperature")
st.line_chart(hourly["temperature_2m"])

# 7-Day Forecast
st.subheader("7-Day Forecast")

df = pd.DataFrame({
    "Max Temp": [fmt(x) for x in daily["temperature_2m_max"]],
    "Min Temp": [fmt(x) for x in daily["temperature_2m_min"]],
    "Rain (mm)": daily["precipitation_sum"],
    "Condition": [get_WMO(code) for code in daily["weathercode"]],
})

st.dataframe(df)