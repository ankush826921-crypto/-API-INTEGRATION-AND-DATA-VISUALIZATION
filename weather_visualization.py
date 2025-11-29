#!/usr/bin/env python3
"""
weather_visualization.py
Fetch hourly temperature for the last 7 days from Open-Meteo, save CSV, and create visualization PNGs and a simple HTML dashboard.

Usage:
    python weather_visualization.py

By default it uses New Delhi coordinates (lat=28.6139, lon=77.2090). Change lat/lon below as needed.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

# ---------- CONFIG ----------
LATITUDE = 28.6139   # New Delhi; change as needed
LONGITUDE = 77.2090
DAYS = 7             # how many past days to fetch
OUTPUT_DIR = "output_weather"
# ----------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

def build_dates(days):
    """Return start_date, end_date strings in YYYY-MM-DD format for the last `days` days (end = today)."""
    end = datetime.utcnow().date()   # use UTC to match API expected dates
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()

def fetch_open_meteo(lat, lon, start_date, end_date):
    """
    Use Open-Meteo API to fetch hourly temperature_2m for given date range.
    API docs: https://open-meteo.com/ (no API key)
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "UTC"   # we'll handle timezone conversion later if needed
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()

def json_to_dataframe(j):
    """Convert open-meteo JSON hourly data to pandas DataFrame (datetime, temp)."""
    hourly = j.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    df = pd.DataFrame({"time_utc": pd.to_datetime(times), "temperature_C": temps})
    # set index
    df = df.set_index("time_utc")
    return df

def save_csv(df, outdir):
    fn = os.path.join(outdir, "hourly_temperature.csv")
    df.to_csv(fn, index=True)
    print("Saved CSV:", fn)
    return fn

def plot_timeseries(df, outdir):
    # Plot hourly temperature time series
    plt.figure(figsize=(14,5))
    plt.plot(df.index, df["temperature_C"])
    plt.title("Hourly Temperature (°C) — Last {} days".format(DAYS))
    plt.xlabel("UTC Time")
    plt.ylabel("Temperature (°C)")
    plt.tight_layout()
    timeseries_path = os.path.join(outdir, "hourly_temperature.png")
    plt.savefig(timeseries_path, dpi=150)
    plt.close()
    print("Saved time series plot:", timeseries_path)
    return timeseries_path

def plot_daily_avg(df, outdir):
    # Resample to daily average
    daily = df.resample("D").mean()
    plt.figure(figsize=(8,5))
    plt.bar(daily.index.strftime("%Y-%m-%d"), daily["temperature_C"])
    plt.title("Daily Average Temperature (°C)")
    plt.xlabel("Date")
    plt.ylabel("Avg Temp (°C)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    daily_path = os.path.join(outdir, "daily_avg_temperature.png")
    plt.savefig(daily_path, dpi=150)
    plt.close()
    print("Saved daily avg plot:", daily_path)
    return daily_path

def create_html_dashboard(images, outdir):
    html = f"""
    <html>
      <head><meta charset="utf-8"><title>Weather Dashboard</title></head>
      <body>
        <h1>Weather Visualization Dashboard</h1>
        <p>Location: lat={LATITUDE}, lon={LONGITUDE} | Last {DAYS} days</p>
    """
    for img in images:
        html += f'<div style="margin-bottom:20px;"><img src="{os.path.basename(img)}" style="max-width:900px; width:100%"></div>\n'
    html += """
      </body>
    </html>
    """
    html_path = os.path.join(outdir, "dashboard.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    # copy images into output dir unchanged (they already are)
    print("Saved dashboard HTML:", html_path)
    return html_path

def main():
    start_date, end_date = build_dates(DAYS)
    print("Fetching data from", start_date, "to", end_date)
    try:
        data_json = fetch_open_meteo(LATITUDE, LONGITUDE, start_date, end_date)
    except Exception as e:
        print("Error fetching data:", e)
        return

    df = json_to_dataframe(data_json)
    if df.empty:
        print("No data returned.")
        return

    csv_path = save_csv(df, OUTPUT_DIR)
    img1 = plot_timeseries(df, OUTPUT_DIR)
    img2 = plot_daily_avg(df, OUTPUT_DIR)
    html_path = create_html_dashboard([img1, img2], OUTPUT_DIR)

    print("\nAll done. Outputs in folder:", OUTPUT_DIR)
    print(" - CSV:", csv_path)
    print(" - Plots:", img1, img2)
    print(" - Dashboard:", html_path)

if __name__ == "__main__":
    main()
