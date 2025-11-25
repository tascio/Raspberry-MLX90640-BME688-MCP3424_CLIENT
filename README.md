# Raspberry Pi 4 Monitoring System (Thermal, Power & Environmental)

## Overview
This project implements a complete monitoring platform built on **Raspberry Pi 4 (Debian 13 Trixie)** with a **Flask-based backend**, a **web client**, and full Dockerization. It is designed to monitor hardware under test—in this case, **WET White Rabbit boards for the KM3NeT project**—by collecting thermal, environmental, power, and device-level data.

The system integrates multiple sensors, maintains high‑frequency data acquisition using multithreaded adapters, stores time‑series data inside **RedisTimeSeries**, and exposes both **REST API endpoints** and a **WebSocket** channel for real‑time thermal streaming.

---

## Features
### ✔ Thermal Imaging
- Sensor: **MLX90640** thermal camera
- Data streamed via **WebSocket** (high‑frequency array streaming)
- Dedicated Docker container for thermal streaming service

### ✔ Environmental Monitoring
- Sensor: **BME688** with measurement of:
  - Temperature
  - Humidity
  - Pressure
  - Gas/IAQ values
  - Altitude estimation
- Data stored in **RedisTimeSeries** via threaded Flask adapter

### ✔ Power Monitoring
- ADC Module: **MCP3424**
- Measures:
  - Current consumption
  - Voltage input/output
- Accessed through dedicated multithreaded adapter
- Data stored in **RedisTimeSeries**

### ✔ DUT (Device Under Test) Monitoring
- Target device: **WET White Rabbit board — KM3NeT**
- Flask adapter connects periodically over **SSH** to collect:
  - On‑board sensor temperatures
  - Any custom system commands required

### ✔ Programmable Power Supply Integration
- Adapter connecting via **serial** to a laboratory power supply
- Allows reading power state and controlling PSU parameters feeding the WET board

### ✔ Redis Time-Series Storage
All adapters record measurements to **RedisTimeSeries**, running in its own container.

---

## Architecture
The system is divided into **server** and **client** components.

### **Backend (Server Docker Stack)**
The Raspberry Pi runs three main containers:

```
┌──────────────────────────┐      ┌──────────────────────────┐
│  Flask REST API Server   │      │  MLX90640 WebSocket Srv  │
│  - BME688 adapter        │      │  - thermal stream        │
│  - MCP3424 adapter       │      │                          │
│  - PSU serial adapter    │      └──────────────────────────┘
│  - WET SSH adapter       │
└───────────┬──────────────┘
            │ RedisTS write
            ▼
┌──────────────────────────┐
│   RedisTimeSeries DB     │
└──────────────────────────┘
```

### **Frontend (Client Docker)**
A separate container implements:
- Flask web client
- Real‑time dashboard UI
- REST/API/WebSocket aggregation
- Configuration web interface for:
  - IP of WET White Rabbit board
  - IP of backend servers
  - Triggering backend ARP configuration

When the user changes the WET target IP, the client contacts the server which executes:
- An `sshpass` procedure
- Connects to the host
- Updates the **ARP table** with IP + MAC provided

---

## Data Flow Summary
```
Sensors → Adapters (threaded) → RedisTimeSeries → REST/WebSocket → Client Dashboard
WET board → SSH Adapter → RedisTS → Client Dashboard
PSU → Serial Adapter → RedisTS → Client Dashboard
```

Thermal camera (MLX90640) bypasses Redis to avoid heavy storage load and streams **live** over a WebSocket.

---

## Technologies Used
### Hardware
- Raspberry Pi 4
- MLX90640 thermal camera
- BME688 environmental sensor
- MCP3424 ADC (power measurement)
- Laboratory power supply (serial‑controlled)
- WET White Rabbit KM3NeT board

### Software
- **Debian 13 Trixie**
- **Python 3 / Flask**
- **Flask-SocketIO (WebSocket)**
- **RedisTimeSeries**
- **sshpass** for remote command automation
- **Docker + docker-compose**

---

## Docker Layout
```
backend-rest/        → Flask REST API server
backend-mlx90640/    → WebSocket thermal streaming
redis/               → RedisTimeSeries instance
client/              → Web client dashboard
```

Each container includes its own adapter logic where applicable.

---

## Client Interface
The web dashboard includes:
- Real‑time thermal camera viewer
- Real‑time charts (temperature, humidity, IAQ, voltage, current)
- System info from WET board via SSH
- Controls for configuring server IPs
- Controls for configuring WET board IP
- Button to perform ARP table update via server

---
