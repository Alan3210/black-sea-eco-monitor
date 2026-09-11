# System Architecture

## High-Level Overview


                    DATA SOURCES

        Satellite       AIS        News
            |            |          |
            |            |          |
            ↓            ↓          ↓


              DATA COLLECTION LAYER


                        ↓


                 AI AGENT SYSTEM


        News Agent
        Social Agent
        Satellite Agent
        Maritime Agent
        Verification Agent


                        ↓


              ENVIRONMENTAL EVENT DATABASE

                    PostgreSQL
                    + PostGIS


                        ↓


                    API LAYER


                        ↓


             GEOSPATIAL VISUALIZATION


                    God's Eye View


                        ↓


                 Human Operator


---

# Core Components

## 1. Data Collectors

Responsible for obtaining information from external sources.

Examples:

- satellite APIs;
- RSS feeds;
- maritime data providers;
- environmental databases.

---

## 2. AI Agents

Agents transform raw information into structured environmental events.

Example:

Raw data:

"Several users report oil smell near beach"

↓

AI analysis:


Type:
pollution_event

Location:
Anapa

Confidence:
0.65


---

## 3. Event Database

Stores normalized environmental events.

Example:


Event

id
type
location
timestamp
severity
confidence
sources


---

## 4. Visualization Layer

God's Eye View provides:

- 3D Earth visualization;
- layers;
- object tracking;
- operator interface.

---

# Design Principle

The environmental intelligence system should remain independent from the visualization layer.

God's Eye View is treated as a visualization client.

The AI/data platform should be reusable by:

- web applications;
- mobile applications;
- VR environments;
- analytical dashboards.