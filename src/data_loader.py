
import pandas as pd
import numpy as np

def load_cpcb_csv(filepath):
    df = pd.read_csv(filepath, encoding='utf-8')
    
    col_map = {
        "Timestamp": "datetime",
        "PM2.5 (µg/m³)": "pm25",
        "PM10 (µg/m³)": "pm10",
        "NO2 (µg/m³)": "no2",
        "Ozone (µg/m³)": "o3",
        "CO (mg/m³)": "co"
    }
    df.rename(columns=col_map, inplace=True)
    
    df["datetime"] = pd.to_datetime(df["datetime"], dayfirst=True, errors="coerce")
    df.dropna(subset=["datetime"], inplace=True)
    
    for col in ["pm25", "pm10", "no2", "o3", "co"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df.loc[df["pm25"] < 0, "pm25"] = np.nan
    df.loc[df["pm25"] > 1500, "pm25"] = np.nan
    
    df.sort_values("datetime", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def merge_years(filepaths):
    dfs = [load_cpcb_csv(fp) for fp in filepaths]
    merged = pd.concat(dfs, ignore_index=True)
    merged.drop_duplicates(subset=["datetime"], inplace=True)
    merged.sort_values("datetime", inplace=True)
    merged.reset_index(drop=True, inplace=True)
    return merged


def add_time_features(df):
    """Add derived time columns useful for trend analysis."""
    df["date"] = df["datetime"].dt.date
    df["year"] = df["datetime"].dt.year
    df["month"] = df["datetime"].dt.month
    df["month_name"] = df["datetime"].dt.strftime("%b")
    df["hour"] = df["datetime"].dt.hour
    df["day_of_week"] = df["datetime"].dt.dayofweek  # 0=Monday
    df["weekday_name"] = df["datetime"].dt.strftime("%A")
    df["is_weekend"] = df["day_of_week"].isin([5, 6])
    df["season"] = df["month"].map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
        10: "Post-Monsoon", 11: "Post-Monsoon"
    })
    return df


def resample_daily(df, pollutants=["pm25", "pm10", "no2", "o3", "co"]):
    """
    Resample hourly data to daily means.
    AQI should be calculated from 24-hour averages for PM2.5 and PM10.
    """
    available = [p for p in pollutants if p in df.columns]
    daily = df.groupby("date")[available].mean().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    return daily