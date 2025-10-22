Cambridge Terahertz System 300 Device Management - Requirements Document
Executive Summary
The Cambridge Terahertz System 300 Device Management (DM) project requires a robust, web-based application for configuring, monitoring, and managing CTHz System 300 imaging devices. The application will be hosted directly on the device's Yocto-based environment and serve as the operational backbone for setup, security, and integration into broader Security Operations (SecOps) workflows.

Project Overview
Objectives
Rapid Deployment: Securely bring up the imaging system in minutes

Operational Control: Enable users to rapidly configure, monitor, and troubleshoot the imaging system

Integration: Enable integration with VMS and Security Operations (SecOps)

Development Phases
The project will be delivered in three phases:

MVP: Basic functionality with manual processes

Phase 1: Enhanced automation and advanced features

Phase 2: Enterprise-grade scalability and cloud integration

Functional Requirements
MVP Scope (Priority P0)
Platform & Deployment
Operating System: Yocto-based build

Backend: Python 3.x with FastAPI

Database: SQLite storage

Service Discovery: mDNSResponder (Bonjour) for local device discovery

Service Management: Secure systemd service configuration

Authentication & Security
Authentication: JWT-based authentication

Authorization: Role-based access control (Owner/Admin/Monitor)

First-time Setup: System locked until Owner/Admin account created and strong password set

Security: HTTPS/TLS everywhere, DoS hardening, CSRF protection

Device & Station Management
Device Information: Model, SW/HW version, location, neighborhood/group name

Station Grouping: Default 3 devices per station with CRUD operations

Status Monitoring: Aggregated station status view

Software Updates: Manual software update via file upload

Discovery & Pairing
Manual Discovery: mDNS/Bonjour browse/resolve using CLI wrapper

Pairing Flow: Manual pairing with enable/disable discovery setting

Network Requirement: Devices must be on the same subnet

Sensor Integration
Communication: HTTPS communication with sensors

Control Operations: Start/stop scan, calibration trigger, calibration image retrieval

Data Retrieval: Time-based scan retrieval (/scans/{time})

Buffer Configuration: Configure image buffer duration for motion-triggered scans

Policy Engine
Rule Engine: Basic If-Then-Else logic using JSONLogic

Default Policies: Pre-configured rules for guns, knives, explosives

Action Hooks: UI alerts, VMS integration calls, motion-triggered scan support

Monitoring & Alerts
Status API: Device/station status monitoring

Error Handling: Critical error notifications in UI

Audit Logging: Comprehensive audit log API

Configuration Management (CFG P0 Items)
CFG-001: Imager information (name, location, model, versions, admin info)

CFG-002: Browser interface for configuration

CFG-003: Login screen with welcome information

CFG-005: Dynamic IP via DHCP configuration

CFG-006: WiFi radio on/off control

CFG-007: WiFi configuration (SSID, WPA2/3, Channel)

CFG-008: Admin configuration (username, password)

CFG-012: Imager status/summary tab

CFG-013: Local storage server configuration

CFG-015: NTP client configuration

CFG-017: CTHz 3D parameters (FOV, ROI, FPS)

Third-Party Integrations
VMS Integration: Genetec VMS adapter (single POC integration)

Biometric Integration: Minimal biometric hook (event POST)

Phase 1 Scope (Priority P1)
Enhanced Discovery
Automatic inter-device and intra-device discovery

Auto-pairing workflows with admin approval

Advanced Security
Optional mTLS between manager and sensors

LDAP/SSO integration

2FA authentication

Enhanced Monitoring
Real-time device/station status via WebSocket or SSE

Expanded metrics and health reporting

Policy monitoring dashboard

Software Management
Automated OTA updates via HTTPS with package verification

Rollback capability

Extended Integrations
Additional VMS platform integrations

Enhanced biometric API integration

Phase 2 Scope (Priority P2)
Enterprise Features
Centralized multi-site device management portal

Cloud sync for configuration, policies, and audit logs

Multi-language UI support

WCAG accessibility compliance

Advanced Analytics
Historical data visualizations

Anomaly detection reports

Integration with external threat intelligence feeds

Extended Integrations
ONVIF support for camera interoperability

Additional third-party analytics platforms

Technical Requirements
System Architecture
Pattern: Device-hosted FastAPI application (ASGI) served by Uvicorn

UI Framework: Bootstrap + HTMX/Alpine.js for responsive design

API Design: Clean separation of UI, API/Services, Integration Adapters, and Persistence

Database: SQLite with migration path to PostgreSQL for future phases

API Specifications
Sensor API Endpoints (Client-provided)
GET /health - Health check

GET /device-info - Device information

POST /scan/start - Start scanning

POST /scan/stop - Stop scanning

POST /calibrate/start - Start calibration

GET /calibration/{id} - Get calibration image

GET /status - Device status

GET /scans/{time} - Time-based scan retrieval

POST /config/image-buffer - Configure motion-trigger buffer duration

Device Management API Endpoints
GET /api/discovery/scan - Scan for devices

POST /api/discovery/resolve - Resolve device details

POST /api/discovery/pair - Pair with device

GET /api/devices - List devices

POST /api/devices - Create device

PUT /api/devices/{id} - Update device

DELETE /api/devices/{id} - Delete device

GET /api/stations - List stations

POST /api/stations - Create station

PUT /api/stations/{id} - Update station

DELETE /api/stations/{id} - Delete station

Security Requirements
TLS: All communication over HTTPS (TLS 1.2+)

Authentication: JWT-based sessions with token refresh

Password Security: Passlib password hashing

DoS Protection: Disable ICMP ping, minimal open ports

CSRF Protection: Configure session security in FastAPI

Performance Requirements
Boot Time: Target 60 seconds (flexible for MVP)

Response Time: Web interface responsive within 2 seconds

Heartbeat: Default 5-minute interval (configurable 1-5 minutes)

FPS: 1-2 fps sufficient for MVP (to be validated)

Observability Requirements
Logging: JSON-structured application logs

Audit Trail: Authentication events, device pairings, policy triggers, admin actions

Log Rotation: Managed at OS level

Monitoring: Optional Sentry/remote syslog hooks (Phase 1+)

Data Management Requirements
Database Schema
Users: User accounts, roles, permissions

Devices: Device registry and configuration

Stations: Station topology and grouping

Policies: Policy definitions and rules

Audit Logs: Comprehensive audit trail

Discovery Cache: Device discovery information

Data Retention
Audit Logs: Configurable retention period

Device Data: Persistent device configuration

Scan Data: Configurable retention based on storage capacity

Integration Requirements
VMS Integration
Genetec: Primary VMS integration for MVP

Protocol: REST API integration

Events: Push threat detection events and metadata

Security: Encrypted credentials at rest

Biometric Integration
Protocol: HTTP POST to configured endpoint

Events: Detection events with basic metadata

Security: Configurable authentication

Network Requirements
Connectivity: Ethernet and WiFi support

IP Configuration: DHCP (default) and static IP support

Network Discovery: mDNS/Bonjour for local network detection

Firewall: Minimal open ports for security

Testing Requirements
Unit Testing
API endpoint testing

Policy engine testing

mDNS parsing and discovery testing

Integration Testing
Simulated sensor API testing

VMS integration mocks

End-to-end workflow testing

Test Environment
Raspberry Pi/simulator with mDNS advertisement

Stubbed sensor API endpoints

Isolated network environment for testing

Deployment Requirements
System Requirements
OS: Yocto-based embedded Linux

Python: Python 3.x runtime with pip modules

Storage: Sufficient space for SQLite database and logs

Memory: Adequate RAM for FastAPI application

Installation Process
Service Setup: systemd service configuration

Environment: Secure environment variables

File Structure: Organized folder structure for configs/logs/database

Permissions: Appropriate file and directory permissions

Configuration Management
Network: WiFi and Ethernet configuration

Time Sync: NTP client configuration

Storage: Local and cloud storage options

Security: Certificate management and TLS configuration

Compliance Requirements
Security Compliance
Data Protection: Secure storage of sensitive information

Access Control: Role-based access enforcement

Audit Trail: Comprehensive logging for compliance

Encryption: Data encryption at rest and in transit

Accessibility (Phase 2)
WCAG: Web Content Accessibility Guidelines compliance

Multi-language: Support for multiple languages

Responsive Design: Support for various devices and screen sizes

Success Criteria
MVP Success Criteria
Rapid Setup: Device operational within 5 minutes of first connection

Basic Operations: Successful scan start/stop and calibration

Integration: Working Genetec VMS integration

Security: Secure authentication and role-based access

Monitoring: Real-time device status and basic alerting

Phase 1 Success Criteria
Automation: Automated device discovery and pairing

Updates: Successful OTA update deployment and rollback

Enhanced Security: LDAP integration and mTLS communication

Monitoring: Real-time status updates and comprehensive metrics

Phase 2 Success Criteria
Scalability: Multi-site management capability

Analytics: Historical reporting and anomaly detection

Compliance: Full audit compliance and accessibility features

Integration: ONVIF support and extended third-party integrations

Constraints and Assumptions
Technical Constraints
Hardware: Limited by Yocto-based embedded environment

Storage: SQLite limitations for large-scale deployments

Network: Local subnet limitation for device discovery

Performance: Embedded system performance limitations

Business Constraints
Timeline: MVP delivery within specified timeframe

Resources: Development team size and expertise

Budget: Hardware and licensing constraints

Compliance: Industry-specific requirements

Assumptions
Client Responsibilities: Sensor API availability and functionality

Network Environment: Stable network connectivity

Hardware Reliability: Reliable embedded hardware platform

User Training: Basic technical competency of end users