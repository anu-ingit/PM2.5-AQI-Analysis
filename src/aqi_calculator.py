# src/aqi_calculator.py

import numpy as np
import pandas as pd

# India NAQI breakpoints (CPCB 2014 standard)
# Format: {pollutant: [(BPLo, BPHi, ILo, IHi), ...]}

NAQI_BREAKPOINTS = {
    "pm25": [
        (0.0, 30.0, 0, 50),
        (30.0, 60.0, 51, 100),
        (60.0, 90.0, 101, 200),
        (90.0, 120.0, 201, 300),
        (120.0, 250.0, 301, 400),
        (250.0, 380.0, 401, 500),
    ],
    "pm10": [
        (0, 50, 0, 50),
        (50, 100, 51, 100),
        (100, 250, 101, 200),
        (250, 350, 201, 300),
        (350, 430, 301, 400),
        (430, 600, 401, 500),
    ],
    "no2": [
        (0, 40, 0, 50),
        (40, 80, 51, 100),
        (80, 180, 101, 200),
        (180, 280, 201, 300),
        (280, 400, 301, 400),
        (400, 800, 401, 500),
    ],
    "o3": [
        (0, 50, 0, 50),
        (50, 100, 51, 100),
        (100, 168, 101, 200),
        (168, 208, 201, 300),
        (208, 748, 301, 400),
        (748, 1000, 401, 500),
    ],
    "co": [  # mg/m³ NOT µg/m³
        (0.0, 1.0, 0, 50),
        (1.0, 2.0, 51, 100),
        (2.0, 10.0, 101, 200),
        (10.0, 17.0, 201, 300),
        (17.0, 34.0, 301, 400),
        (34.0, 46.0, 401, 500),
    ],
    "so2": [
        (0, 40, 0, 50),
        (40, 80, 51, 100),
        (80, 380, 101, 200),
        (380, 800, 201, 300),
        (800, 1600, 301, 400),
        (1600, 2100, 401, 500),
    ],
}

AQI_CATEGORIES = [
    (0, 50, "Good", "#00e400"),
    (51, 100, "Satisfactory", "#ffff00"),
    (101, 200, "Moderate", "#ff7e00"),
    (201, 300, "Poor", "#ff0000"),
    (301, 400, "Very Poor", "#8f3f97"),
    (401, 500, "Severe", "#7e0023"),
]


def sub_index(concentration, pollutant):
    """Calculate sub-AQI for a single pollutant concentration."""
    if pd.isna(concentration) or concentration < 0:
        return np.nan
    
    breakpoints = NAQI_BREAKPOINTS.get(pollutant)
    if not breakpoints:
        return np.nan
    
    for (bp_lo, bp_hi, i_lo, i_hi) in breakpoints:
        if bp_lo <= concentration <= bp_hi:
            aqi = ((i_hi - i_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + i_lo
            return round(aqi)
    
    # Exceeds highest breakpoint
    return 500


def calculate_aqi(row, pollutants=None):
    """
    Calculate overall AQI as max of all available sub-indices.
    Pass a DataFrame row with pollutant concentration columns.
    """
    if pollutants is None:
        pollutants = ["pm25", "pm10", "no2", "o3", "co", "so2"]
    
    sub_indices = {}
    for p in pollutants:
        if p in row.index and not pd.isna(row[p]):
            sub_indices[p] = sub_index(row[p], p)
    
    if not sub_indices:
        return np.nan, None
    
    dominant_pollutant = max(sub_indices, key=sub_indices.get)
    overall_aqi = sub_indices[dominant_pollutant]
    
    return overall_aqi, dominant_pollutant


def get_aqi_category(aqi):
    """Return category label and color hex for a given AQI value."""
    if pd.isna(aqi):
        return "Unknown", "#cccccc"
    for lo, hi, label, color in AQI_CATEGORIES:
        if lo <= aqi <= hi:
            return label, color
    return "Severe", "#7e0023"


def apply_aqi_to_dataframe(df):
    """Apply AQI calculation to every row of a daily-averaged DataFrame."""
    results = df.apply(calculate_aqi, axis=1)
    df["aqi"] = results.apply(lambda x: x[0])
    df["dominant_pollutant"] = results.apply(lambda x: x[1])
    df["aqi_category"] = df["aqi"].apply(lambda x: get_aqi_category(x)[0])
    df["aqi_color"] = df["aqi"].apply(lambda x: get_aqi_category(x)[1])
    return df