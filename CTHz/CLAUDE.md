# claude.md - Cambridge Terahertz Device Management System

You are an expert full-stack developer building a comprehensive device management application for Cambridge Terahertz System 300 imaging devices. This system manages terahertz threat detection sensors deployed in security environments with a hierarchical group-station-device architecture.

## Project Overview

**System**: Web-based device management platform for CTHz System 300 threat detection sensors
**Architecture**: FastAPI backend + SQLite database + Bootstrap/HTMX frontend
**Deployment**: On-device hosting with Yocto Linux + Docker development environment
**Security**: JWT authentication, role-based access, HTTPS/TLS communication
**Integration**: VMS systems, biometric platforms, external monitoring

## Core Architecture

### Hierarchical Data Model
```
Groups (Top Level - multiple screening locations)
├── Screening Stations (3-device clusters for 360° coverage)
│   ├── CTHz Imager 1 (Manager role)
│   ├── CTHz Imager 2 (Sensor role) 
│   └── CTHz Imager 3 (Sensor role)
└── Standalone Imagers (not in stations)
```

### Technology Stack
- **Backend**: FastAPI 0.104+ with async/await, Uvicorn ASGI server
- **Database**: SQLite (MVP) with SQLAlchemy ORM, PostgreSQL migration path
- **Frontend**: Bootstrap 5 + HTMX for reactive UI, Jinja2 templates
- **Security**: JWT tokens, bcrypt passwords, role-based access control
- **Discovery**: mDNS/Bonjour for local device detection with manual pairing
- **Communication**: HTTPS client (httpx) for sensor API integration

### Application Structure
```
cthz-device-manager/
├── src/
│   ├── main.py                    # FastAPI app entry point
│   ├── config/
│   │   └── settings.py           # Configuration management
│   ├── auth/
│   │   ├── models.py             # User/Role models
│   │   ├── auth.py               # JWT, RBAC, password handling
│   │   └── routes.py             # Authentication endpoints
│   ├── groups/
│   │   ├── models.py             # Group management models
│   │   ├── service.py            # Group business logic
│   │   └── routes.py             # Group CRUD APIs
│   ├── stations/
│   │   ├── models.py             # Station models (3-device clusters)
│   │   ├── service.py            # Station orchestration
│   │   └── routes.py             # Station management APIs
│   ├── devices/
│   │   ├── models.py             # Device/Imager models
│   │   ├── discovery.py          # mDNS device discovery
│   │   ├── service.py            # Device lifecycle management
│   │   └── routes.py             # Device management APIs
│   ├── sensors/
│   │   ├── client.py             # HTTPS sensor communication
│   │   ├── proxy.py              # API proxy to hardware layer
│   │   └── routes.py             # Sensor control endpoints
│   ├── policies/
│   │   ├── models.py             # Policy storage
│   │   ├── engine.py             # JSONLogic rule evaluation
│   │   └── routes.py             # Policy CRUD APIs
│   ├── config_mgmt/
│   │   ├── models.py             # Device configuration storage
│   │   ├── handlers.py           # Configuration validation/application
│   │   └── routes.py             # Unified configuration API
│   ├── monitoring/
│   │   ├── health.py             # Health check service
│   │   ├── alerts.py             # Alert management with criticality
│   │   ├── audit.py              # Audit logging service
│   │   └── routes.py             # Monitoring APIs
│   ├── integrations/
│   │   ├── vms/
│   │   │   ├── base.py           # VMS adapter interface
│   │   │   ├── genetec.py        # Genetec integration
│   │   │   └── milestone.py      # Milestone integration
│   │   ├── biometric.py          # Biometric system integration
│   │   └── routes.py             # Integration management
│   ├── storage/
│   │   ├── archive.py            # Archive server integration
│   │   ├── backup.py             # System backup service
│   │   └── routes.py             # Storage management APIs
│   ├── database/
│   │   ├── connection.py         # SQLAlchemy setup
│   │   ├── models.py             # Base model classes
│   │   └── migrations/           # Database migrations
│   ├── utils/
│   │   ├── exceptions.py         # Custom exception hierarchy
│   │   ├── logging.py            # Structured JSON logging
│   │   ├── security.py           # Security utilities
│   │   └── validation.py         # Input validation helpers
│   ├── static/                   # CSS, JS, images
│   └── templates/                # Jinja2 HTML templates
│       ├── base.html
│       ├── setup/                # First-time setup wizard
│       ├── dashboard/            # Main dashboard
│       ├── groups/               # Group management UI
│       ├── stations/             # Station management UI  
│       ├── devices/              # Device management UI
│       ├── policies/             # Policy management UI
│       └── monitoring/           # Monitoring & alerts UI
```

## Database Schema

### Core Entities
```sql
-- Authentication & Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(16) NOT NULL CHECK (role IN ('owner', 'admin', 'monitor')),
    email VARCHAR(128),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Hierarchical Organization
CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(64) NOT NULL,
    description TEXT,
    location VARCHAR(128),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER REFERENCES groups(id),
    name VARCHAR(64) NOT NULL,
    location VARCHAR(128),
    device_count INTEGER DEFAULT 0,
    max_devices INTEGER DEFAULT 3,
    coverage_angle INTEGER DEFAULT 360,
    manager_device_id INTEGER REFERENCES devices(id),
    status VARCHAR(16) DEFAULT 'inactive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(64) NOT NULL,
    model VARCHAR(32) NOT NULL DEFAULT 'CTHz-300',
    serial_number VARCHAR(64) UNIQUE,
    firmware_version VARCHAR(16),
    hardware_version VARCHAR(16),
    ip_address INET,
    mac_address VARCHAR(17),
    group_id INTEGER REFERENCES groups(id),
    station_id INTEGER REFERENCES stations(id),
    device_role VARCHAR(16) DEFAULT 'sensor' CHECK (device_role IN ('manager', 'sensor')),
    location VARCHAR(128),
    timezone VARCHAR(32) DEFAULT 'UTC',
    status VARCHAR(16) DEFAULT 'offline',
    last_seen TIMESTAMP,
    last_calibrated TIMESTAMP,
    discovery_enabled BOOLEAN DEFAULT FALSE,
    ssid_broadcast BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Policy Management
CREATE TABLE policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(64) NOT NULL,
    description TEXT,
    conditions JSON NOT NULL,        -- JSONLogic conditions
    actions JSON NOT NULL,           -- Action configuration
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_system_policy BOOLEAN DEFAULT FALSE,
    applies_to VARCHAR(16) DEFAULT 'all' CHECK (applies_to IN ('group', 'station', 'device', 'all')),
    target_id INTEGER,               -- group_id, station_id, or device_id
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuration Management
CREATE TABLE device_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER REFERENCES devices(id),
    configuration JSON NOT NULL,     -- Complete device configuration
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    applied_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monitoring & Events
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL CHECK (severity IN ('critical', 'warning', 'info')),
    title VARCHAR(128) NOT NULL,
    message TEXT NOT NULL,
    source_type VARCHAR(16) CHECK (source_type IN ('group', 'station', 'device', 'system')),
    source_id INTEGER,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(32),
    resource_id VARCHAR(64),
    details JSON,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(128)
);

-- Storage & Archive
CREATE TABLE archive_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(64) NOT NULL,
    server_url VARCHAR(256) NOT NULL,
    auth_type VARCHAR(16) DEFAULT 'token',
    credentials_encrypted TEXT,      -- Encrypted credentials
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Integration Management
CREATE TABLE integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    integration_type VARCHAR(32) NOT NULL,
    name VARCHAR(64) NOT NULL,
    config JSON NOT NULL,           -- Integration-specific configuration
    credentials_encrypted TEXT,      -- Encrypted connection credentials
    is_active BOOLEAN DEFAULT TRUE,
    last_test TIMESTAMP,
    test_result VARCHAR(16),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Core Features Implementation

### Authentication & Security
```python
# JWT-based authentication with role hierarchy
ROLES = {
    'owner': ['*'],                          # Full system access
    'admin': ['devices.*', 'policies.*', 'config.*', 'monitoring.*'],
    'monitor': ['devices.read', 'monitoring.*']
}

# Security requirements
- Strong password validation (12+ chars, mixed case, numbers, symbols)
- JWT tokens with 8-hour expiration and refresh capability
- Role-based endpoint protection with decorators
- Audit logging for all administrative actions
- HTTPS/TLS mandatory (self-signed certificates for MVP)
```

### Device Discovery & Management
```python
# mDNS-based device discovery with security restrictions
- Service advertisement: _cthz-device._tcp.local
- Manual pairing process with admin approval
- SSID broadcast disabled by default
- Discovery restricted to authorized applications
- Device roles: 'manager' (station coordinator) or 'sensor'
- Status tracking: online/offline/error/maintenance
```

### Configuration Management
```python
# Unified configuration API covering all P0 CFG items:
CFG_SECTIONS = {
    'imager_info': {          # CFG-001: Device identification
        'name', 'location', 'model', 'timezone', 'admin_contact'
    },
    'network': {
        'wifi': {             # CFG-002: WiFi configuration  
            'enabled', 'ssid', 'security_type', 'hidden_ssid'
        },
        'lan': {              # CFG-003: Ethernet configuration
            'dhcp_enabled', 'ip_address', 'subnet_mask', 'gateway', 'dns'
        }
    },
    'location': {
        'gps': {              # CFG-006: GPS settings
            'enabled', 'latitude', 'longitude', 'altitude', 'source'
        }
    },
    'system': {
        'ntp': {              # CFG-012: Time synchronization
            'enabled', 'servers', 'sync_interval', 'timezone_auto'
        },
        'heartbeat': {        # CFG-013: Health monitoring
            'enabled', 'interval_minutes', 'endpoint', 'timeout'
        }
    },
    'storage': {              # CFG-008: Data storage
        'local_path', 'max_local_gb', 'archive_enabled', 'retention_days'
    },
    'media': {
        'video_audio': {      # CFG-015: Media capture
            'video_enabled', 'resolution', 'fps', 'audio_enabled'
        }
    },
    'detection': {
        'cthz_3d': {          # CFG-017: Detection parameters
            'fov_degrees', 'roi', 'scan_fps', 'sensitivity', 'threat_types'
        }
    }
}
```

### Policy Engine
```python
# JSONLogic-based rule evaluation with default threat policies
DEFAULT_POLICIES = [
    {
        'name': 'Firearm Detection',
        'conditions': {
            'and': [
                {'==': [{'var': 'threat_type'}, 'firearm']},
                {'>': [{'var': 'confidence'}, 0.85]}
            ]
        },
        'actions': [
            {'type': 'ui_alert', 'severity': 'critical'},
            {'type': 'vms_event', 'priority': 'high'},
            {'type': 'trigger_scan', 'duration': 30}
        ]
    }
]

# Action types supported:
- ui_alert: Browser notifications with color coding
- vms_event: Push to configured VMS systems  
- email_notification: SMTP alerts
- webhook_call: HTTP POST to external systems
- trigger_scan: Motion-activated scanning
```

### Monitoring & Alerts
```python
# Alert criticality with color coding
ALERT_LEVELS = {
    'critical': {'color': 'red', 'priority': 1},      # Immediate attention required
    'warning': {'color': 'yellow', 'priority': 2},    # Needs attention soon
    'info': {'color': 'blue', 'priority': 3}          # Informational only
}

# System monitoring features:
- Device health aggregation (group → station → device)
- Storage monitoring with configurable thresholds (default 75%)
- Calibration status tracking with overdue alerts
- Network connectivity monitoring
- Integration health checks
```

### Time Management
```python
# All internal storage in UTC with local display
TIME_HANDLING = {
    'storage': 'UTC',                    # All database timestamps
    'api_responses': 'UTC',              # API returns UTC
    'ui_display': 'local_timezone',      # UI shows local time
    'logs': 'UTC',                       # All log entries in UTC
    'exports': 'UTC_and_local'           # Include both for exports
}

# UI toggle for UTC/Local time display in notifications and alerts
```

## Hardware Layer Integration

### Required APIs from CTHz Team
```python
# Core sensor control endpoints (31 total)
HARDWARE_LAYER_APIS = {
    '/health': 'GET',                              # 5s timeout
    '/device-info': 'GET',                         # Device identification
    '/status': 'GET',                              # Current operational state
    '/scan/start': 'POST',                         # Initiate threat scan
    '/scan/stop': 'POST',                          # Stop current scan
    '/scans/{scan_id}': 'GET',                     # Retrieve scan results
    '/scans/recent': 'GET',                        # Query recent scans
    '/calibration/start': 'POST',                  # Start calibration
    '/calibration/{cal_id}': 'GET',                # Calibration results
    '/motion/status': 'GET',                       # Motion detection state
    '/config/device': 'GET/PUT',                   # Device configuration
    '/system/logs': 'GET',                         # Diagnostic logs
}

# Data formats required from hardware layer:
- Threat detection results with confidence scores (0.0-1.0)
- Calibration pass/fail status with accuracy metrics
- Motion detection events with timestamps
- System health metrics (temperature, CPU, memory, storage)
- Configuration validation and application status
```

### Proxy Pattern Implementation
```python
# Device Management APIs proxy to Hardware Layer with added business logic
class SensorProxy:
    async def start_scan(self, device_id: str, scan_request: ScanRequest):
        # 1. Authenticate user and check permissions
        # 2. Validate device is online and available
        # 3. Apply policy-based scan parameters
        # 4. Forward request to hardware layer
        # 5. Track scan in database for audit
        # 6. Return response with correlation ID
        
    async def get_scan_results(self, device_id: str, scan_id: str):
        # 1. Retrieve results from hardware layer
        # 2. Evaluate results against active policies
        # 3. Trigger policy actions if threats detected
        # 4. Update monitoring metrics
        # 5. Log activity for compliance
        # 6. Return enriched results to client
```

## Development Environment

### Docker Compose Setup
```yaml
# Multi-device simulation environment
services:
  cthz-manager:
    build: .
    ports: ["8000:8000"]
    environment:
      DEVICE_MODE: manager
      DEVICE_ID: manager-001
    networks:
      cthz_network:
        ipv4_address: 192.168.1.10

  cthz-sensor-1:
    build: .
    ports: ["8001:8000"]
    environment:
      DEVICE_MODE: sensor
      DEVICE_ID: sensor-001
    networks:
      cthz_network:
        ipv4_address: 192.168.1.11

  # Additional sensors for testing multi-device scenarios

networks:
  cthz_network:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.1.0/24
```

### Testing Strategy
```python
# Comprehensive test coverage
TEST_CATEGORIES = {
    'unit': ['auth', 'policies', 'device_management', 'configuration'],
    'integration': ['database', 'sensor_communication', 'vms_integration'],
    'e2e': ['setup_flow', 'device_discovery', 'threat_response_workflow'],
    'security': ['authentication', 'authorization', 'input_validation'],
    'performance': ['api_response_times', 'concurrent_users', 'database_queries']
}
```

## Implementation Priorities

### MVP Phase (Weeks 1-6)
1. **Core Infrastructure**: FastAPI app, SQLite database, JWT authentication
2. **Device Management**: Discovery, pairing, basic configuration
3. **Group/Station Management**: Hierarchical organization with CRUD operations
4. **Policy Engine**: JSONLogic evaluation with default threat policies  
5. **Monitoring Dashboard**: Device status, alerts, basic reporting
6. **Hardware Integration**: Sensor proxy APIs for scan control

### Phase 1 (Weeks 7-10)  
1. **VMS Integration**: Genetec adapter with event publishing
2. **Advanced Monitoring**: Storage alerts, calibration tracking
3. **Archive Integration**: Secure credential storage, automated archival
4. **Enhanced Security**: mTLS, advanced authentication options
5. **Audit & Compliance**: Exportable logs, comprehensive audit trail

### Phase 2 (Weeks 11-14)
1. **Multi-site Deployment**: Centralized management portal
2. **Advanced Analytics**: Historical reporting, trend analysis  
3. **Mobile Interface**: Responsive design for tablets/phones
4. **Integration Expansion**: Additional VMS platforms, biometric systems
5. **Performance Optimization**: Caching, database optimization

## Security Implementation

### Network Security
```python
# HTTPS/TLS requirements
- TLS 1.3 preferred, 1.2 minimum
- Self-signed certificates acceptable for MVP
- Certificate validation for sensor communication
- mTLS support for production deployments

# Access Control
- JWT tokens with configurable expiration (default 8 hours)
- Role-based API endpoint protection
- Session management with automatic timeout
- Audit logging for all administrative actions

# Data Protection  
- Encrypted credential storage using Fernet symmetric encryption
- Password hashing with bcrypt (12 rounds minimum)
- Input validation and sanitization for all user inputs
- Rate limiting on authentication endpoints
```

### Operational Security
```python
# Device Security
- SSID broadcast disabled by default
- Device discovery restricted to authorized applications
- Secure pairing process with admin approval
- Network segmentation recommendations

# System Hardening
- Minimal open ports (80→443 redirect, 443 HTTPS, 5353 mDNS)
- Disable unnecessary services
- Regular security updates via managed update process
- Backup encryption for sensitive configuration data
```

## Key Design Patterns

### Repository Pattern
- Clean separation of data access logic
- Database abstraction for future PostgreSQL migration
- Consistent CRUD operations across all entities

### Service Layer Pattern  
- Business logic separated from HTTP routing
- Reusable services for device orchestration
- Transaction management for multi-table operations

### Observer Pattern
- Event-driven policy evaluation
- Decoupled alert generation and notification
- Extensible integration architecture

### Proxy Pattern
- Hardware Layer API abstraction
- Request/response transformation
- Error handling and retry logic

Focus on building a robust, secure foundation that can scale from single-device deployments to multi-site enterprise installations. Prioritize reliability and user experience while maintaining clear separation of concerns between UI, business logic, and data persistence layers.