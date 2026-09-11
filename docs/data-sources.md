# Data Sources

## Overview

Black Sea Eco Monitor combines multiple open data sources to create a unified environmental intelligence system.

Each data source provides only partial information.

The platform combines multiple independent signals to improve detection accuracy and confidence estimation.

---

# Data Architecture


External Sources

  |
  ↓

Data Collectors

  |
  ↓

Data Normalization

  |
  ↓

AI Analysis

  |
  ↓

Environmental Events Database

  |
  ↓

Geospatial Visualization


---

# 1. Satellite Data

## Purpose

Satellite data provides large-scale environmental observation capabilities.

Potential applications:

- wildfire detection;
- water surface anomalies;
- pollution monitoring;
- coastal changes;
- vegetation analysis.

---

## NASA FIRMS

Status:
Planned / First integration candidate

Purpose:

Active fire and thermal anomaly monitoring.

Provides:

- fire locations;
- detection time;
- satellite source;
- confidence information.

Use cases:

- wildfire monitoring;
- coastal fire risks;
- emergency awareness.


---

## Sentinel Satellite Program

Status:
Research

Purpose:

Earth observation using Copernicus satellites.

Potential applications:

- water quality analysis;
- oil spill detection;
- coastal monitoring;
- environmental changes.


---

## Landsat

Status:
Research

Purpose:

Historical and long-term environmental analysis.

Potential applications:

- coastline changes;
- ecosystem monitoring;
- water surface analysis.

---

# 2. Maritime Data

## AIS Vessel Tracking

Status:
Planned

Purpose:

Monitoring ship activity in the Black Sea.

Potential applications:

- vessel tracking;
- unusual stops;
- possible pollution sources;
- maritime risk analysis.

Data examples:


Vessel

ID:
123456789

Position:
Latitude / Longitude

Speed:

Course:

Timestamp:


---

# 3. Weather Data

## Purpose

Weather conditions are important for environmental event analysis.

Examples:

- wildfire propagation;
- pollution movement;
- storm events;
- coastal risks.

Potential parameters:

- wind speed;
- wind direction;
- precipitation;
- temperature;
- sea conditions.

---

# 4. Open Source Intelligence (OSINT)

## Purpose

Collect publicly available information about environmental events.

Sources:

- news websites;
- RSS feeds;
- official announcements;
- public reports;
- social networks.

---

# News Monitoring Agent

Purpose:

Detect:

- oil spills;
- fires;
- chemical pollution;
- ecological incidents.

Input:

Articles and reports.

Output:

Structured environmental events.


Example:


Event:

Type:
Pollution

Location:
Anapa coastline

Source:
News article

Confidence:
0.65


---

# Social Monitoring Agent

Purpose:

Analyze public reports and detect early signals.

Possible sources:

- Telegram channels;
- public social media;
- community reports.

Important:

Social information is treated as an early indicator, not confirmed evidence.

---

# 5. Environmental Databases

Potential future sources:

- government environmental monitoring;
- scientific datasets;
- research organizations;
- marine biology databases.

---

# 6. Data Confidence Model

Each environmental event receives a confidence score.

Example:


Event:
Possible oil pollution

Signals:

Satellite anomaly:
0.8

News reports:
0.6

Social reports:
0.4

AIS correlation:
0.7

Final confidence:
0.68


---

# 7. Environmental Event Model

All incoming information is converted into a unified format.

Example:

```json
{
  "id": "event_001",

  "type": "pollution",

  "category": "oil_spill",

  "location": {
    "latitude": 44.62,
    "longitude": 37.83
  },

  "severity": "medium",

  "confidence": 0.72,

  "sources": [
    "satellite",
    "news",
    "ais"
  ],

  "timestamp": "2026-09-11"
}
Initial MVP Data Sources

The first prototype will focus on:

1. NASA FIRMS

Purpose:
Wildfire monitoring.

2. AIS

Purpose:
Ship tracking and maritime activity.

3. News Agent

Purpose:
Environmental incident discovery.

4. Manual Event Database

Purpose:
Testing visualization and AI analysis.

Future Expansion

Possible additions:

Sentinel-2 automated analysis;
water quality monitoring;
IoT sensors;
drone imagery;
marine biodiversity data;
climate models.