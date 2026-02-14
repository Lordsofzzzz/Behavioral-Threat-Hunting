# Behavioral Threat Hunting Platform

## Overview
The Behavioral Threat Hunting Platform is a containerized system designed to detect malicious activity in web application traffic by analyzing HTTP access logs in real time. The system performs structured log ingestion, session-based behavioral analysis, and rule-driven detection to generate alerts from web server logs.

The platform currently operates as the backend detection engine of a larger security monitoring architecture and is intended to evolve into a full SOC-style monitoring system with API and dashboard layers.

## Project Objectives
The main goal of this project is to build a modular detection engine capable of monitoring NGINX-style logs and identifying malicious activity. The system focuses on real-time analysis, behavioral tracking, and scalable containerized deployment. Planned detection capabilities include directory traversal detection, SQL injection detection, cross-site scripting detection, and behavioral anomaly detection.

## Current Architecture
The platform consists of two primary containers. The traffic generator simulates realistic web requests and writes logs into a shared Docker volume. The behavioral detection engine reads these logs continuously, analyzes them, and produces alerts based on detection rules. The shared volume allows real-time log streaming between containers.

## Implemented Components

### Traffic Generator
Located in `scripts/log_generator.py`, the traffic generator simulates web traffic by producing both normal and malicious HTTP requests. It writes structured NGINX-style logs to `/app/logs/access.log`, allowing the detection engine to operate without a real web server during development.

### Behavioral Detection Engine
The detection engine resides inside `src/bth_web/` and represents the core of the platform. It processes logs through a pipeline that includes ingestion, normalization, session tracking, detection logic, and alert output.

Key modules include:
- `ingest/nginx_parser.py` for parsing raw log lines
- `normalize/schema.py` for defining event structures
- `sessionize/sessions.py` for behavioral session tracking
- `features/http_features.py` for extracting indicators
- `detection/rules.py` for detection logic
- `reporting/report.py` for generating outputs
- `cli.py` for real-time monitoring

### Docker Deployment
The system is fully containerized. The `bth-generator` container generates logs while the `bth-monitor` container analyzes them. Both containers share a Docker volume mounted at `/app/logs`, enabling real-time analysis without external dependencies.

## Detection Workflow
When deployed, the detection engine continuously reads web logs. Each log line is parsed into a structured event containing source IP, URL, timestamp, status code, and user agent. Events are grouped into behavioral sessions based on source IP and user agent. Behavioral metrics such as request rate and access patterns are tracked over time. Detection rules are then applied to identify suspicious activity, and alerts are generated when threats are detected.

## Current Detection Capabilities
The system currently detects directory traversal attempts by identifying suspicious path traversal patterns in URLs. Additional detection rules for SQL injection, XSS, command injection, and anomaly scoring are planned for future development.

## Running the Platform
Build the containers using:

## How to Run

Make sure Docker is installed and running on your system.

1. Build the containers:

``docker compose build``


2. Start the platform:

``docker compose up``


The `bth-generator` container will begin generating simulated web traffic, and the `bth-monitor` container will analyze the logs and print alerts in real time.

3. Stop the platform:

``docker compose down``