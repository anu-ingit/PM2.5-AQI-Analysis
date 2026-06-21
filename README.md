# PM2.5 & AQI Analysis — Kolkata

An independent environmental data project analyzing air quality trends in Kolkata using real-world monitoring data from CPCB's Rabindra Bharati University station (2022–2024).

## What this project does

- Ingests daily pollutant data (PM2.5, PM10, NO₂, O₃, CO) from CPCB CAAQMS
- Calculates daily AQI using India's official NAQI breakpoint formula (CPCB 2014)
- Analyzes seasonal trends, weekday vs weekend differences, and festival-related spikes
- Visualizes pollutant correlations and AQI category distributions
- Presents everything in an interactive Streamlit dashboard with date filters

## Tools & Libraries

Python · Pandas · Plotly · Seaborn · Streamlit · GitHub

## Data Source

CPCB CAAQMS — Rabindra Bharati University, Kolkata (2022–2024)
https://app.cpcbccr.com/ccr/

## AQI Standard

India NAQI (CPCB 2014). PM2.5 exceedance referenced against WHO Global Air Quality Guidelines 2021 (24-hr limit: 15 µg/m³).

## Run locally

```bash
git clone https://github.com/anu-ingit/PM2.5-AQI-Analysis.git
cd PM2.5-AQI-Analysis
python -m venv venv && source venv/Scripts/activate
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Live Dashboard

[PM2.5 AQI ANALYSIS
](https://pm25-aqi-analysis-dashboard.streamlit.app/)

## Status

🟡 In progress — data pipeline complete, dashboard in development
