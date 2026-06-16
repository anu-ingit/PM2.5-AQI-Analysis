
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.data_loader import load_cpcb_csv, add_time_features, resample_daily
from src.aqi_calculator import apply_aqi_to_dataframe, plot_correlation_heatmap
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India AQI Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load data (cache for performance) ────────────────────────────────────────
@st.cache_data
def load_data(city):
    path_map = {
        "Kolkata": "data/processed/kolkata_daily.csv",
        "Delhi":   "data/processed/delhi_daily.csv",
        "Mumbai":  "data/processed/mumbai_daily.csv",
    }
    df = pd.read_csv(path_map[city], parse_dates=["date"])
    df = add_time_features(df)
    df = apply_aqi_to_dataframe(df)
    return df

# ── Sidebar controls ──────────────────────────────────────────────────────────
st.sidebar.title("🌫️ AQI Dashboard")
st.sidebar.markdown("Air Quality Index — India")

city = st.sidebar.selectbox("Select City", ["Kolkata", "Delhi", "Mumbai"])

df = load_data(city)

min_date = df["date"].min().date()
max_date = df["date"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

pollutant_choice = st.sidebar.selectbox(
    "Pollutant for trend analysis",
    ["pm25", "pm10", "no2", "o3", "co"]
)

# ── Filter data ───────────────────────────────────────────────────────────────
if len(date_range) == 2:
    start, end = date_range
    mask = (df["date"].dt.date >= start) & (df["date"].dt.date <= end)
    filtered = df[mask].copy()
else:
    filtered = df.copy()

# ── Header KPI cards ──────────────────────────────────────────────────────────
st.title(f"Air Quality Dashboard — {city}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    avg_aqi = filtered["aqi"].mean()
    st.metric("Mean AQI", f"{avg_aqi:.0f}")
with col2:
    avg_pm25 = filtered["pm25"].mean() if "pm25" in filtered.columns else None
    who_exceedance = (filtered["pm25"] > 15).sum() if "pm25" in filtered.columns else 0
    st.metric("Mean PM2.5 (µg/m³)", f"{avg_pm25:.1f}" if avg_pm25 else "N/A",
              delta=f"{who_exceedance} days > WHO limit",
              delta_color="inverse")
with col3:
    good_days = (filtered["aqi"] <= 50).sum()
    total_days = filtered["aqi"].notna().sum()
    st.metric("Good Air Days", f"{good_days}/{total_days}")
with col4:
    severe_days = (filtered["aqi"] > 300).sum()
    st.metric("Severe Days", f"{severe_days}",
              delta_color="inverse")

st.divider()

# ── AQI Trend Chart ────────────────────────────────────────────────────────────
st.subheader("AQI Trend")

fig_aqi = go.Figure()
fig_aqi.add_trace(go.Scatter(
    x=filtered["date"],
    y=filtered["aqi"],
    mode="lines",
    line=dict(color="#e07b39", width=1.5),
    fill="tozeroy",
    fillcolor="rgba(224, 123, 57, 0.15)",
    name="AQI"
))
fig_aqi.add_hline(y=100, line_dash="dot", line_color="gray", annotation_text="Moderate")
fig_aqi.add_hline(y=200, line_dash="dot", line_color="orange", annotation_text="Poor")
fig_aqi.add_hline(y=300, line_dash="dot", line_color="red", annotation_text="Very Poor")
fig_aqi.update_layout(
    height=350, template="plotly_white",
    yaxis_title="AQI", xaxis_title="Date",
    margin=dict(l=40, r=20, t=20, b=40)
)
st.plotly_chart(fig_aqi, use_container_width=True)

# ── Two-column layout ─────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Seasonal Distribution")
    season_order = ["Winter", "Spring", "Monsoon", "Post-Monsoon"]
    season_data = filtered.groupby("season")[pollutant_choice].mean().reindex(season_order)
    
    fig_season = px.bar(
        season_data.reset_index(),
        x="season", y=pollutant_choice,
        color=pollutant_choice,
        color_continuous_scale="Oranges",
        labels={pollutant_choice: f"{pollutant_choice.upper()} µg/m³"},
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

# ── Correlation Heatmap ────────────────────────────────────────────────────────
st.subheader("Pollutant Correlation Heatmap")

pollutants_available = [p for p in ["pm25","pm10","no2","o3","co","so2"]
                        if p in filtered.columns]
corr = filtered[pollutants_available].corr()

fig_corr, ax = plt.subplots(figsize=(7, 5))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f",
            cmap="RdYlGn", center=0, vmin=-1, vmax=1,
            linewidths=0.5, ax=ax)
ax.set_title("Pollutant Correlations")
plt.tight_layout()
st.pyplot(fig_corr)

# ── Raw data toggle ────────────────────────────────────────────────────────────
with st.expander("Show raw data table"):
    st.dataframe(
        filtered[["date","pm25","pm10","no2","o3","co","aqi","aqi_category"]].head(200),
        use_container_width=True
    )
    
    csv = filtered.to_csv(index=False)
    st.download_button("Download filtered CSV", csv, "aqi_filtered.csv", "text/csv")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Data sources: CPCB CAAQMS, OpenAQ. "
    "AQI calculated using India NAQI standard (CPCB 2014). "
    "WHO reference: Global Air Quality Guidelines 2021."
)