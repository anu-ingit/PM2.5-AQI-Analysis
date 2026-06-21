import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.data_loader import add_time_features

st.set_page_config(page_title="Kolkata AQI Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/kolkata_daily.csv")
    df["datetime"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df = add_time_features(df)
    return df

df = load_data()

st.sidebar.title("🌫️ AQI Dashboard")

min_date = df["datetime"].min().date()
max_date = df["datetime"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start, end = date_range
    mask = (df["datetime"].dt.date >= start) & (df["datetime"].dt.date <= end)
    filtered = df[mask].copy()
else:
    filtered = df.copy()

pollutant_choice = st.sidebar.selectbox(
    "Pollutant for trend analysis",
    ["pm25", "pm10", "no2", "o3", "co"]
)

st.title("Air Quality Dashboard — Kolkata")
st.write(f"Showing {len(filtered)} rows")
st.divider()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Mean AQI", f"{filtered['aqi'].mean():.0f}")
with col2:
    avg_pm25 = filtered["pm25"].mean()
    who_exceedance = (filtered["pm25"] > 15).sum()
    st.metric("Mean PM2.5 (µg/m³)", f"{avg_pm25:.1f}",
              delta=f"{who_exceedance} days > WHO limit",
              delta_color="inverse")
with col3:
    good_days = (filtered["aqi"] <= 50).sum()
    total_days = filtered["aqi"].notna().sum()
    st.metric("Good Air Days", f"{good_days}/{total_days}")
with col4:
    severe_days = (filtered["aqi"] > 300).sum()
    st.metric("Severe Days", f"{severe_days}", delta_color="inverse")

st.divider()
st.subheader("AQI Trend")

fig_aqi = go.Figure()
fig_aqi.add_trace(go.Scatter(
    x=filtered["datetime"], y=filtered["aqi"],
    mode="lines",
    line=dict(color="#e07b39", width=1.5),
    fill="tozeroy",
    fillcolor="rgba(224, 123, 57, 0.15)",
    name="AQI"
))
fig_aqi.add_hline(y=100, line_dash="dot", line_color="gray", annotation_text="Moderate")
fig_aqi.add_hline(y=200, line_dash="dot", line_color="orange", annotation_text="Poor")
fig_aqi.add_hline(y=300, line_dash="dot", line_color="red", annotation_text="Very Poor")
fig_aqi.update_layout(height=350, template="plotly_white",
                      yaxis_title="AQI", xaxis_title="Date",
                      margin=dict(l=40, r=20, t=20, b=40))
st.plotly_chart(fig_aqi, use_container_width=True)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Seasonal Distribution")
    season_order = ["Winter", "Spring", "Monsoon", "Post-Monsoon"]
    season_data = filtered.groupby("season")[pollutant_choice].mean().reindex(season_order)
    fig_season = px.bar(
        season_data.reset_index(), x="season", y=pollutant_choice,
        color=pollutant_choice, color_continuous_scale="Oranges",
        title=f"Seasonal Mean {pollutant_choice.upper()}"
    )
    fig_season.update_layout(height=320, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_season, use_container_width=True)

with col_right:
    st.subheader("Weekday vs Weekend")
    wd_data = filtered.groupby("is_weekend")[pollutant_choice].mean().reset_index()
    wd_data["day_type"] = wd_data["is_weekend"].map({True: "Weekend", False: "Weekday"})
    fig_wd = px.bar(
        wd_data, x="day_type", y=pollutant_choice,
        color="day_type",
        color_discrete_map={"Weekday": "#4c72b0", "Weekend": "#dd8452"},
        title=f"Weekday vs Weekend {pollutant_choice.upper()}"
    )
    fig_wd.update_layout(height=320, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_wd, use_container_width=True)