"""
Data acquisition layer for Eco-Climate Intelligence.
Uses Open-Meteo Historical API — no API key needed, works with all Python versions.
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import warnings
warnings.filterwarnings("ignore")


@st.cache_data(ttl=86400, show_spinner=False)
def get_coordinates(city_name: str):
    """
    Geocode a city name into lat/lon using OpenStreetMap Nominatim.
    Returns (lat, lon, display_name) or (None, None, None) on failure.
    """
    try:
        geolocator = Nominatim(user_agent="eco_climate_intel_v1", timeout=10)
        location   = geolocator.geocode(city_name, language="en")
        if location:
            display = location.address.split(",")[0].strip()
            return round(location.latitude, 4), round(location.longitude, 4), display
    except (GeocoderTimedOut, GeocoderServiceError, Exception):
        pass
    return None, None, None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_weather_data(lat: float, lon: float, years: int = 3):
    """
    Fetch daily climate data from Open-Meteo Historical Weather API.
    Returns a cleaned DataFrame or None on failure.
    """
    end_date   = datetime.now() - timedelta(days=5)   # API has ~5 day lag
    start_date = end_date - timedelta(days=365 * years)

    params = {
        "latitude":        lat,
        "longitude":       lon,
        "start_date":      start_date.strftime("%Y-%m-%d"),
        "end_date":        end_date.strftime("%Y-%m-%d"),
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
            "windspeed_10m_max",
            "shortwave_radiation_sum",
        ],
        "timezone":        "auto",
        "wind_speed_unit": "kmh",
    }

    try:
        resp = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        st.error("Request timed out. Check your internet connection and try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {e}")
        return None

    daily = data.get("daily", {})
    if not daily or "time" not in daily:
        return None

    df = pd.DataFrame({
        "time": pd.to_datetime(daily["time"]),
        "tmax": daily.get("temperature_2m_max"),
        "tmin": daily.get("temperature_2m_min"),
        "tavg": daily.get("temperature_2m_mean"),
        "prcp": daily.get("precipitation_sum"),
        "wspd": daily.get("windspeed_10m_max"),
        "tsun": daily.get("shortwave_radiation_sum"),
    })
    df = df.set_index("time")

    if len(df) < 90:
        return None

    # Derive tavg if missing
    if df["tavg"].isna().all():
        df["tavg"] = (df["tmax"] + df["tmin"]) / 2

    # Fill gaps
    df = df.interpolate(method="linear", limit=14).ffill().bfill()

    # Convenience columns
    df["month"] = df.index.month
    df["year"]  = df.index.year
    df["doy"]   = df.index.dayofyear
    df["tavg_7d"] = df["tavg"].rolling(7, min_periods=1).mean()

    return df


def latest_conditions(df: pd.DataFrame) -> dict:
    """Summarise most recent 7 days for the header strip."""
    if df is None or df.empty:
        return {}
    recent = df.tail(7)
    return {
        "avg_temp":   round(recent["tavg"].mean(), 1),
        "max_temp":   round(recent["tmax"].max(), 1),
        "min_temp":   round(recent["tmin"].min(), 1),
        "total_prcp": round(recent["prcp"].sum(), 1),
        "avg_wspd":   round(recent["wspd"].mean(), 1) if "wspd" in df.columns else 0.0,
    }
