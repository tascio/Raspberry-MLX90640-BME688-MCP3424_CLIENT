# Raspberry Pi 4 Monitoring System (Thermal, Power & Environmental)

## Overview

This project implements a complete monitoring platform built on
**Raspberry Pi 4 (Debian 13 Trixie)** with a **Flask-based backend**, a
**web client**, and full Dockerization.\
It is designed to monitor hardware under test --- specifically **WET
White Rabbit boards for the KM3NeT project** --- by collecting thermal,
environmental, power, and device-level data.

The backend integrates multiple sensors, performs high-frequency
acquisition via multithreaded adapters, stores time-series data in
**RedisTimeSeries**, and exposes both **REST APIs** and a **WebSocket**
channel for real-time thermal streaming.

Both backend and frontend are now served behind a **production-grade
NGINX + Gunicorn stack**, with **Gunicorn running asynchronously using
Eventlet**, supporting WebSocket communication.

------------------------------------------------------------------------

## Features

### ✔ Thermal Imaging

-   Sensor: **MLX90640** thermal camera\
-   Streamed live via **WebSocket** (high-frequency array streaming)\
-   Runs inside dedicated Docker service (Gunicorn async + Eventlet)

### ✔ Environmental Monitoring

-   Sensor: **BME688** (Temperature, Humidity, Pressure, Gas/IAQ,
    Altitude)\
-   Adapter runs inside backend container\
-   Data stored in **RedisTimeSeries**

### ✔ Power Monitoring

-   ADC Module: **MCP3424**\
-   Measures current & voltage\
-   Multithreaded adapter stores data in RedisTimeSeries

### ✔ DUT (Device Under Test) Monitoring --- WET White Rabbit (KM3NeT)

-   Backend connects periodically via **SSH**\
-   Reads:
    -   On-board temperature sensors\
    -   Custom commands and diagnostics

### ✔ Programmable Power Supply Integration

-   Serial adapter communicates with lab PSU\
-   Reads electrical parameters\
-   Supports remote control of supply powering the WET board

### ✔ RedisTimeSeries Storage

All adapters store high-rate telemetry in a dedicated
**RedisTimeSeries** container.

------------------------------------------------------------------------

## Architecture

The system is split into **server** and **client** stacks, both now
running through:

-   **NGINX** as a reverse proxy\
-   **Gunicorn async (Eventlet)** as the Python application server\
-   Full WebSocket compatibility through the async stack

------------------------------------------------------------------------

### **Backend (Server Docker Stack)**

     ┌───────────────────────────────┐     ┌──────────────────────────────┐
     │      NGINX Reverse Proxy      │     │   MLX90640 WebSocket Server  │
     │         (HTTP / WS)           │     │   - Gunicorn Eventlet        │
     └──────────────┬────────────────┘     └──────────────────────────────┘
                    │ proxy_pass
     ┌──────────────▼────────────────┐
     │    Gunicorn (async) + Flask   │
     │    - REST API                 │
     │    - BME688 adapter           │
     │    - MCP3424 adapter          │
     │    - PSU serial adapter       │
     │    - WET SSH adapter          │
     └──────────────┬────────────────┘
                    │ writes
                    ▼
     ┌───────────────────────────────┐
     │       RedisTimeSeries DB      │
     └───────────────────────────────┘

------------------------------------------------------------------------

### **Frontend (Client Docker Stack)**

A separate container includes:

-   **NGINX** serving static UI and reverse proxying API/WebSocket\
-   **Gunicorn async (Eventlet)** running Flask client app\
-   Real-time dashboard\
-   Aggregated REST + WebSocket data streams\
-   Configuration UI for:
    -   Backend server IPs\
    -   WET White Rabbit board IP\
    -   Triggering backend ARP table updates

When the WET board IP is updated, the client triggers a backend workflow
that:

1.  Runs an automated **sshpass** command\
2.  Logs into the specified host\
3.  Updates **ARP tables** with new IP/MAC mapping

------------------------------------------------------------------------

## Data Flow Summary

     Sensors → Threaded Adapters → RedisTS → REST/WebSocket → Client Dashboard
     WET board → SSH Adapter → RedisTS → Client Dashboard
     PSU → Serial Adapter → RedisTS → Client Dashboard
     Thermal Camera → WebSocket Stream → Client Dashboard (no Redis)

The **MLX90640** thermal stream bypasses Redis to avoid heavy data
storage and is sent **directly via WebSocket**.

------------------------------------------------------------------------

## Technologies Used

### Hardware

-   Raspberry Pi 4\
-   MLX90640 thermal sensor\
-   BME688 environmental sensor\
-   MCP3424 ADC\
-   Lab PSU (serial-controlled)\
-   WET White Rabbit MN3NeT board

### Software Stack

-   **Debian 13 Trixie**
-   **Python 3 / Flask**
-   **Gunicorn (async worker: Eventlet)**
-   **NGINX reverse proxy (client & server)**
-   **Flask-SocketIO** (WebSocket)
-   **RedisTimeSeries**
-   **Docker + Docker Compose**
-   **sshpass** automation

------------------------------------------------------------------------

## Docker Layout

     backend-rest/        → Flask backend (Gunicorn + Eventlet)
     backend-mlx90640/    → Thermal WebSocket server
     redis/               → RedisTimeSeries
     client/              → Web dashboard (NGINX + Gunicorn)

Each backend component integrates its respective adapters.

------------------------------------------------------------------------

## Client Interface

The dashboard provides:

-   **Real-time thermal viewer**
-   **Live charts** for:
    -   Temperature\
    -   Humidity\
    -   IAQ\
    -   Voltage\
    -   Current\
-   **System info** from WET board via SSH
-   Backend IP configuration
-   WET board IP configuration
-   Trigger for backend ARP update
