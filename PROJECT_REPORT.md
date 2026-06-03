# Middleware Data Processing Platform — Project Report

**Date:** June 2026  
**Author:** Melisa Sudee  
**Repository:** FinalProje  
**Branch:** main  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture & Design](#2-architecture--design)
3. [Implementation Details](#3-implementation-details)
4. [Challenges & Solutions](#4-challenges--solutions)
5. [Test Results & Metrics](#5-test-results--metrics)
6. [Deployment & Operations](#6-deployment--operations)
7. [Future Improvements](#7-future-improvements)
8. [Appendix](#8-appendix)

---

## 1. Project Overview

### 1.1 Description

A production-grade **financial data middleware platform** that ingests transaction logs, anonymizes sensitive fields, enriches records with risk scoring, and exposes them through a role-based REST API with a real-time web dashboard.

The system runs as a two-service Docker stack:

| Service | Container | Port | Role |
|---|---|---|---|
| Middleware | `finalproje-middleware` | 5000 | Core API, DB, Dashboard |
| Data Generator | `finalproje-generator` | 5001 | Synthetic load producer |

### 1.2 Goals and Requirements

| Requirement | Status |
|---|---|
| Receive and persist financial transaction logs | ✅ Implemented |
| Anonymize PII (email, credit card, TC ID, phone) | ✅ Implemented |
| Enrich records with risk scores and tags | ✅ Implemented |
| Dual authentication (JWT + API Key) | ✅ Implemented |
| Role-based data export (5 roles, 3 formats) | ✅ Implemented |
| Real-time dashboard with charts | ✅ Implemented |
| GDPR/KVKK compliance management | ✅ Implemented |
| Docker-based deployment with health checks | ✅ Implemented |
| Strategy Pattern for formatters | ✅ Implemented |
| Log classification system | ✅ Implemented |

### 1.3 Scope and Deliverables

- REST API with 29 endpoints
- SQLite database with 9 model tables
- Interactive dashboard (Chart.js, dark/light themes)
- Role-based export panel (Security, Developer, Admin, Auditor, Analyst)
- GDPR/KVKK compliance dashboard
- Anonymization pipeline (4 strategies: mask, hash, redact, email-mask)
- Risk enrichment engine (score 0–100, 4 risk levels)
- Containerized via Docker Compose with resource limits

---

## 2. Architecture & Design

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network (172.20.0.0/16)        │
│                                                         │
│  ┌─────────────────────────┐  ┌──────────────────────┐  │
│  │   data-generator :5001  │  │   middleware :5000   │  │
│  │                         │  │                      │  │
│  │  data_generator.py      │→ │  app.py (Flask)      │  │
│  │  - Synthetic events     │  │  - REST API          │  │
│  │  - POST /api/generate   │  │  - Auth layer        │  │
│  │  - GET /health          │  │  - Process pipeline  │  │
│  │                         │  │  - SQLite DB         │  │
│  └─────────────────────────┘  │  - Dashboard HTML    │  │
│                               └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
               ↑ port 5000 exposed to host
               ↓ browser / curl / clients
```

### 2.2 Data Flow

```
POST /api/process (or /api/batch)
        │
        ▼
   require_auth  ←── JWT token  OR  X-API-KEY header / ?api_key=
        │
        ▼
   anonymize_event()
   ├─ hash: password, secret, token
   ├─ mask: credit_card, tc_id, transaction_id
   ├─ email-mask: *@domain
   └─ redact: phone, phone_number
        │
        ▼
   enrich_event()
   ├─ risk_score  (0-100, amount + error_level driven)
   ├─ risk_level  (LOW / MEDIUM / HIGH / CRITICAL)
   ├─ error_classification  (AUTH_ERROR / FRAUD_ALERT / …)
   ├─ tags  (risk:X, type:X, source:X, status:X)
   └─ analysis  (amount_bucket, is_high_value, trust_score)
        │
        ▼
   LogEntry.from_payload() → db.session.add()
        │
        ▼
   JSON response  {status, data, message}
```

### 2.3 Component Diagram

```
app.py ──────────────────────────────────────────────────
│  Routes: /process, /batch, /stats, /export             │
│          /api/export, /api/dashboard-stats             │
│          /logs/*, /format/*, /auth/login               │
│          /compliance/* (13 endpoints)                  │
│                                                        │
├── auth.py        require_auth decorator                │
│                  JWT + API Key dual check              │
│                                                        │
├── anonymizer.py  PII anonymization pipeline            │
├── enricher.py    Risk scoring + tagging                │
├── formatters.py  Strategy Pattern                      │
│    ├── JSONFormatter                                   │
│    ├── CSVFormatter                                    │
│    ├── HTMLFormatter                                   │
│    ├── SelectiveFormatter (Context)                    │
│    ├── FormatterFactory (backward-compat)              │
│    └── RoleBasedFormatter (dual format support)        │
│                                                        │
├── log_classifier.py  Role-based classification        │
│    ├── LogType Enum  (5 types)                         │
│    ├── Role Enum  (5 roles)                            │
│    └── LogClassifier  (filter + project + detect)     │
│                                                        │
├── models.py      9 SQLAlchemy models                  │
├── extensions.py  db, jwt, migrate, limiter            │
├── config.py      Dev / Production configs             │
├── compliance.py  ComplianceManager (GDPR/KVKK)        │
└── init_compliance.py  DB seed for compliance data     │
```

### 2.4 Design Patterns

#### Strategy Pattern — `formatters.py`

```
Formatter (ABC)
├── format(data) → str          abstract
├── validate(data) → bool       abstract
├── get_content_type() → str    abstract
├── get_file_extension() → str  abstract
└── safe_format(data) → str     template method

Concrete Strategies:
├── JSONFormatter  → application/json  (.json)
├── CSVFormatter   → text/csv          (.csv)
└── HTMLFormatter  → text/html         (.html)

Context: SelectiveFormatter
├── set_strategy(format_type)   runtime swap
├── format(data)                delegates to strategy
├── available_formats()         static, reads registry
└── register(name, formatter)   Open/Closed extension

Registry: _REGISTRY = {"json": …, "csv": …, "html": …}
Factory:  FormatterFactory.get_formatter(fmt)  ← backward compat
Special:  RoleBasedFormatter → handles "dual" (CSV + JSON envelope)
```

#### Role-Based Classification — `log_classifier.py`

```
Role Enum: security | developer | admin | auditor | analyst

Per-role configuration:
┌───────────┬──────────┬───────────────────────────┬─────────────────┐
│ Role      │ Format   │ Field Filter               │ Level Filter    │
├───────────┼──────────┼───────────────────────────┼─────────────────┤
│ security  │ CSV      │ 9 security fields          │ ERROR, CRITICAL │
│ developer │ JSON     │ all fields                 │ ERROR, WARN, CRIT│
│ admin     │ HTML     │ 8 management fields        │ all             │
│ auditor   │ dual     │ all fields                 │ all             │
│ analyst   │ CSV      │ 9 analytics fields         │ all             │
└───────────┴──────────┴───────────────────────────┴─────────────────┘

Pipeline: flatten(log) → level_filter → detect_log_type → project(fields)
```

#### Factory Pattern — `app.py`

```python
def create_app(config_name=None) -> Flask:
    cfg = config.config_by_name.get(config_name, ProductionConfig)
    app = Flask(__name__)
    app.config.from_object(cfg)
    db.init_app(app); jwt.init_app(app)
    migrate.init_app(app, db); limiter.init_app(app)
    with app.app_context(): db.create_all()
    return app

app = create_app()  # module-level instance for Gunicorn
```

---

## 3. Implementation Details

### 3.1 Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.12 |
| Web Framework | Flask | ≥ 3.0.0 |
| ORM | Flask-SQLAlchemy | ≥ 3.0.0 |
| DB Migrations | Flask-Migrate | ≥ 4.0.0 |
| Authentication | Flask-JWT-Extended | ≥ 4.4.0 |
| Rate Limiting | Flask-Limiter | ≥ 3.0.0 |
| Password Hashing | bcrypt | ≥ 4.0.0 |
| HTTP Server | Gunicorn | ≥ 20.1.0 |
| Database | SQLite | (via SQLAlchemy) |
| Containerization | Docker + Compose | 3.9 |
| Frontend Charts | Chart.js | 4.4.0 |
| Fonts | Google Fonts / Inter | — |

### 3.2 Module Descriptions

#### `app.py` (1641 lines)
Core application file. Contains the Flask factory, all route handlers, and the embedded `DASHBOARD_HTML` string (~1200 lines of HTML/CSS/JS). Route groups:
- Core: `/health`, `/process`, `/batch`, `/stats`
- Export: `/export`, `/api/export` (role-based), `/format/<mode>`
- Logs: `/logs/critical`, `/logs/errors`, `/logs/by-risk`
- Dashboard: `/`, `/dashboard`, `/api/dashboard-stats`
- Auth: `/auth/login`
- Compliance: 13 endpoints under `/compliance/*`

#### `anonymizer.py` (116 lines)
PII anonymization pipeline. Four strategies:
- `sha256_hash()` — for passwords and secrets
- `mask_value()` — for credit cards, TC IDs (keeps prefix/suffix)
- `anonymize_email()` — masks local part, keeps domain
- `replace_with_redacted()` — for phones
- `detect_and_redact_patterns()` — regex scan of string values

#### `enricher.py` (159 lines)
Risk scoring and event enrichment:
- `compute_risk_score(amount, error_level)` → 0–100 integer
- `describe_risk(score)` → LOW / MEDIUM / HIGH / CRITICAL
- `classify_error(message, error_level)` → error type label
- `build_tags(event, risk_level, error_class)` → sorted tag list
- `enrich_event(event)` → full enriched dict

Risk score thresholds:
```
Amount < 1,000  → base 10
Amount 1k–5k    → base 40
Amount 5k–20k   → base 75
Amount ≥ 20k    → base 95
ERROR/CRITICAL  → min 85
```

#### `formatters.py` (295 lines)
Strategy Pattern implementation. Three concrete formatters registered in `_REGISTRY`. `SelectiveFormatter` is the Context. `RoleBasedFormatter` wraps context for role-aware output including the `dual` format (auditor): a JSON envelope `{role, record_count, formats: {csv, json}}`.

#### `log_classifier.py` (141 lines)
Role-based log classification. `LogClassifier.classify_by_role()` pipeline:
1. Flatten: merge `payload` dict into top-level fields
2. Filter: keep only allowed error levels for the role
3. Detect: add `log_type` field via `detect_log_type()`
4. Project: keep only role-specified fields (or all if `None`)

#### `models.py` (318 lines)
Nine SQLAlchemy models:

| Model | Table | Purpose |
|---|---|---|
| LogEntry | log_entries | Core transaction log |
| ApiKey | api_keys | Dynamic API key management |
| ComplianceMetric | compliance_metrics | GDPR/KVKK scores |
| DataCategory | data_categories | PII category tracking |
| RtBFRequest | rtbf_requests | Right to be Forgotten |
| ConsentRecord | consent_records | User consent tracking |
| DataAccessLog | data_access_logs | Access audit trail |
| AuditLog | audit_logs | System audit events |
| ComplianceViolation | compliance_violations | Violation tracking |
| ComplianceChecklist | compliance_checklist | GDPR/KVKK checklist |

#### `auth.py` (44 lines)
`require_auth` decorator checks (in order):
1. `X-API-KEY` header OR `?api_key=` query param against env config + DB
2. JWT token via `verify_jwt_in_request(optional=True)`

Either passing grants access; both missing returns 401.

#### `data_generator.py` (230 lines)
Server-mode Flask app on port 5001. Generates synthetic financial transactions with randomized:
- sender/receiver IDs, emails, amounts (10–100,000 USD/EUR/TRY)
- transaction types: PAYMENT, TRANSFER, REFUND, WITHDRAWAL
- error levels: INFO (70%), WARNING (15%), ERROR (10%), CRITICAL (5%)

Sends events to `http://middleware:5000/api/process` with `X-API-KEY` header.

#### `compliance.py` (450 lines)
`ComplianceManager` class orchestrating GDPR/KVKK compliance:
- GDPR score calculation (data minimization, consent, encryption, audit log)
- KVKK score calculation (Turkish regulation equivalent)
- RtBF request lifecycle management
- Violation detection and reporting
- Checklist progress tracking

### 3.3 Code Statistics

| File | Lines | Role |
|---|---|---|
| app.py | 1641 | Core routes + dashboard HTML |
| compliance.py | 450 | GDPR/KVKK manager |
| performance_test.py | 323 | Load testing tool |
| models.py | 318 | DB models (9 tables) |
| formatters.py | 295 | Strategy pattern |
| init_compliance.py | 246 | DB seed data |
| data_generator.py | 230 | Synthetic data server |
| start_containers.py | 182 | Container orchestration helper |
| enricher.py | 159 | Risk scoring engine |
| log_classifier.py | 141 | Role classification |
| anonymizer.py | 116 | PII anonymization |
| config.py | 49 | Env configuration |
| auth.py | 44 | Auth decorator |
| extensions.py | 11 | Flask extension init |
| **Total** | **4276** | |

### 3.4 Key Features

**Real-time Dashboard**
- Chart.js 4.4.0 line, doughnut, and bar charts
- Auto-refresh every 30 seconds with countdown
- Dark/light theme toggle (CSS custom properties)
- 4 metric cards: Total Logs, Critical Alerts, Success Rate, Processing Speed
- 20-minute throughput history (1-minute buckets)
- Risk distribution and transaction type breakdowns

**Role-Based Export Panel**
- 5 role cards (Security Officer, Developer, Admin, Auditor, Analyst)
- Configurable API key input
- Blob download with correct filename and extension
- Button loading state (Exporting… → original text in finally)
- Export is hidden on print (`@media print`)

**Rate Limiting**
- 100/min on `/api/process`
- 50/min on `/api/export`
- In-memory storage (production should use Redis)

**GDPR/KVKK Compliance**
- RtBF request creation and lifecycle (PENDING → IN_PROGRESS → COMPLETED)
- Consent tracking with expiry dates
- Data access logging with IP and user agent
- Audit trail for all compliance actions
- Compliance score dashboard with GDPR and KVKK sub-scores

---

## 4. Challenges & Solutions

### 4.1 Docker Network Isolation

**Problem:** `data-generator` could not resolve `http://middleware:5000` hostname. All generated events silently failed.

**Root Cause:** `data-generator` service was not assigned to `middleware-network` in `docker-compose.yml`, so Docker's internal DNS could not route the name.

**Solution:**
```yaml
# docker-compose.yml — data-generator service
networks:
  - middleware-network   # ← this line was missing
```

**Lesson learned:** Always verify that inter-service communication uses the same named network. Docker DNS only resolves service names within a shared network.

### 4.2 Performance Test 100% Failure

**Problem:** `performance_test.py` was reporting 100% request failure rate.

**Root Cause:** `send_request()` was not including the `X-API-KEY` header. All requests received 401 Unauthorized.

**Solution:** Added `api_key` parameter to `send_request()`:
```python
headers = {"Content-Type": "application/json", "X-API-KEY": api_key}
```

**Lesson learned:** Auth middleware silently rejects requests; check headers first when observing unexpected 4xx responses.

### 4.3 Test Suite 404 on All Endpoints

**Problem:** All pytest tests returned 404 for every route.

**Root Cause:** `conftest.py` called `create_app()` which creates a new Flask instance. Flask routes are registered on the module-level `app` object, not the factory-returned instance.

**Solution:** Changed conftest to import the module-level instance directly:
```python
# conftest.py
from app import app as flask_app   # module-level app, has all routes
flask_app.config.update({...})     # override for tests
```

**Lesson learned:** In Flask, routes are bound to a specific app instance. Factory pattern and module-level `app = create_app()` require careful import strategy in tests.

### 4.4 Dockerfile COPY Failure After Cleanup

**Problem:** `docker compose build` failed because `Dockerfile.middleware` referenced deleted files (`scenarios.py`, `performance_test.py`).

**Solution:** Updated COPY instruction and added new `log_classifier.py`:
```dockerfile
COPY app.py anonymizer.py enricher.py formatters.py log_classifier.py \
     config.py extensions.py models.py auth.py \
     compliance.py init_compliance.py ./
```

**Lesson learned:** Delete file from Dockerfile COPY at the same time as removing the file from the repo.

### 4.5 Factory vs Module-Level Route Registration

**Problem:** Flask's application factory pattern (`create_app()`) conflicts with module-level route registration using `@app.route`. The factory returns a new app object, but decorators run at import time on the module-level `app`.

**Solution:** Use the module-level instance for Gunicorn (`app:app`) while keeping the factory for configuration flexibility. Tests import `app` directly, not through the factory.

**Best Practice:** If the project grows, migrate routes to Blueprints — Blueprints decouple route registration from the app instance and work cleanly with factories.

### 4.6 Dual Format for Auditor Role

**Problem:** The Auditor role needed both CSV (for spreadsheet tools) and JSON (for programmatic access) in a single export.

**Solution:** `RoleBasedFormatter._format_dual()` wraps both representations in a JSON envelope:
```json
{
  "role": "auditor",
  "record_count": 1000,
  "formats": {
    "csv": "...(csv string)...",
    "json": [...array of records...]
  }
}
```

---

## 5. Test Results & Metrics

### 5.1 Unit Tests

```
======================== 5 passed, 6 warnings in 0.19s =========================

tests/test_app.py::test_health_endpoint        PASSED
tests/test_app.py::test_process_endpoint       PASSED
tests/test_auth.py::test_login_success         PASSED
tests/test_auth.py::test_api_key_access        PASSED
tests/test_auth.py::test_unauthorized_access   PASSED
```

**Warnings (non-breaking):**
- 4× `datetime.utcnow()` deprecation (Python 3.12+) — scheduled for fix
- 1× Flask-Limiter in-memory storage warning
- 1× JWT key length warning (test key is intentionally short)

### 5.2 Live System Metrics (June 2026)

```
Total Logs Processed:   1,000
Critical Alerts:          415  (41.5%)
Success Rate:            61.8%
Processing Speed:         0.0 logs/min (idle at report time)

Risk Distribution:
  CRITICAL: 267  (26.7%)
  HIGH:     503  (50.3%)
  MEDIUM:   212  (21.2%)
  LOW:       18  ( 1.8%)
```

### 5.3 Role Export Verification

```bash
# All 5 role endpoints tested with correct content types:
security → text/csv              ✅  HTTP 200
developer → application/json     ✅  HTTP 200
admin → text/html                ✅  HTTP 200
auditor → application/json       ✅  HTTP 200 (dual envelope)
analyst → text/csv               ✅  HTTP 200
```

### 5.4 Security Assessment

| Check | Result |
|---|---|
| SQL Injection | Protected (SQLAlchemy ORM parameterized queries) |
| XSS in HTML export | Protected (`html.escape()` on all cell values) |
| Auth bypass | Protected (both JWT and API key paths validated) |
| Secrets in git | `.secrets.json` in `.gitignore`; removed from tracking |
| Rate limiting | Active (100/min process, 50/min export) |
| Sensitive data in logs | PII anonymized before persistence |
| Credit card masking | 4-digit prefix + suffix visible, middle masked |

### 5.5 Code Quality

| Metric | Value |
|---|---|
| Total Python lines | 4,276 |
| Files | 14 source + 3 test |
| Design patterns used | 3 (Strategy, Factory, Decorator) |
| API endpoints | 29 |
| DB models | 9 |
| Formatter strategies | 3 (+ 1 composite dual) |
| Roles | 5 |
| Anonymization strategies | 4 |

---

## 6. Deployment & Operations

### 6.1 Docker Setup

```yaml
# Two services on a shared bridge network (172.20.0.0/16)
services:
  middleware:
    build: Dockerfile.middleware
    ports: ["5000:5000"]
    resources: { cpus: "2", memory: 1G }
    healthcheck: curl -f http://localhost:5000/health
    restart: unless-stopped

  data-generator:
    build: Dockerfile.generator
    ports: ["5001:5001"]
    depends_on: { middleware: { condition: service_healthy } }
    resources: { cpus: "1", memory: 512M }
    restart: unless-stopped
```

`data-generator` waits for middleware to pass health checks before starting. This prevents connection errors during the gunicorn startup phase.

### 6.2 Configuration

Environment variables (set in `docker-compose.yml`):

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | production | Config class selector |
| `DATABASE_URL` | sqlite:////app/data/middleware.db | DB connection string |
| `JWT_SECRET_KEY` | dev-jwt-secret-key | JWT signing key |
| `API_KEYS` | local-api-key | Comma-separated valid keys |
| `ADMIN_USERNAME` | admin | Dashboard admin login |
| `ADMIN_PASSWORD` | secret | Dashboard admin password |
| `TARGET` | http://middleware:5000/api/process | Generator target URL |
| `COUNT` | 100 | Events per generation run |
| `SCENARIO` | normal | Generation scenario |
| `MODE` | server | Generator mode (server/batch) |

### 6.3 Deployment Guide

```bash
# 1. Clone repository
git clone <repo> && cd FinalProje

# 2. Build and start stack
docker compose up -d --build

# 3. Verify health
docker ps                                    # both containers Up (healthy)
curl http://localhost:5000/health            # {"status":"ok"}

# 4. Trigger data generation
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 100, "scenario": "normal"}'

# 5. Open dashboard
open http://localhost:5000

# 6. Export by role (example)
curl -o security.csv \
  "http://localhost:5000/api/export?role=security&api_key=local-api-key"
```

### 6.4 Monitoring & Logging

**Health check endpoint:** `GET /health` — returns `{"status":"ok","data":{"service":"middleware","uptime":"..."}}`

**Stats endpoint:** `GET /stats` — returns total_logs, critical count, warnings count, by_risk breakdown

**Dashboard stats:** `GET /api/dashboard-stats` — full metrics JSON for Chart.js (no auth required)

**Log persistence:** All processed events stored in SQLite at `/app/data/middleware.db`. Volume-mounted at `./data` for host access.

**Container logs:**
```bash
docker logs finalproje-middleware --tail 50 --follow
docker logs finalproje-generator  --tail 50 --follow
```

**Rebuild after code changes:**
```bash
docker compose up -d --build
```

---

## 7. Future Improvements

### 7.1 Potential Enhancements

| Enhancement | Priority | Effort |
|---|---|---|
| Replace `datetime.utcnow()` with timezone-aware `datetime.now(UTC)` | High | Low |
| Migrate routes to Flask Blueprints | Medium | Medium |
| Add PostgreSQL support (replace SQLite) | Medium | Medium |
| Add Prometheus `/metrics` endpoint | Medium | Low |
| Full test coverage for compliance endpoints | High | Medium |
| Replace in-memory rate limit store with Redis | High | Low |

### 7.2 Scalability Considerations

| Bottleneck | Current State | Recommended Fix |
|---|---|---|
| Database | SQLite (single writer) | PostgreSQL with connection pooling |
| Rate limiter storage | In-memory (per-process) | Redis backend |
| Gunicorn workers | 2 workers | Scale based on CPU cores (2n+1) |
| Log processing | Synchronous | Async queue (Celery + Redis) |
| Dashboard stats | DB query per request | Cache with TTL (Redis) |

### 7.3 Security Upgrades

- Rotate `JWT_SECRET_KEY` and `API_KEYS` via environment secrets management (e.g., Docker Secrets, Vault)
- Add HTTPS/TLS termination (nginx reverse proxy with Let's Encrypt)
- Implement API key expiry and rotation endpoint
- Add CORS policy restrictions for production origins
- Increase JWT key length in test config to suppress `InsecureKeyLengthWarning`

### 7.4 Performance Optimizations

- Add database index on `created_at` in `log_entries` (currently indexed: `transaction_id`, `sender_id`, `error_level`, `risk_level`)
- Paginate `/logs/*` endpoints (currently returns up to 500 records in dashboard-stats)
- Cache dashboard stats (currently computed on every request)
- Use streaming response for large exports (`?limit=` without bound)

---

## 8. Appendix

### 8.1 Source Code Files

```
FinalProje/
├── app.py                    # Core Flask application (1641 lines)
├── anonymizer.py             # PII anonymization (116 lines)
├── auth.py                   # Auth decorator (44 lines)
├── compliance.py             # GDPR/KVKK manager (450 lines)
├── config.py                 # Configuration classes (49 lines)
├── data_generator.py         # Synthetic data server (230 lines)
├── enricher.py               # Risk scoring engine (159 lines)
├── extensions.py             # Flask extension init (11 lines)
├── formatters.py             # Strategy Pattern formatters (295 lines)
├── init_compliance.py        # DB seed data (246 lines)
├── log_classifier.py         # Role-based classification (141 lines)
├── models.py                 # SQLAlchemy models (318 lines)
├── performance_test.py       # Load testing tool (323 lines)
├── start_containers.py       # Container helper (182 lines)
├── Dockerfile.middleware      # Middleware container build
├── Dockerfile.generator       # Generator container build
├── docker-compose.yml        # Stack orchestration
├── requirements_middleware.txt
├── requirements_generator.txt
├── requirements_dev.txt
└── tests/
    ├── conftest.py           # Pytest fixtures
    ├── test_app.py           # Core endpoint tests
    └── test_auth.py          # Auth tests
```

### 8.2 API Quick Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Service health check |
| GET | `/` `/dashboard` | No | Web dashboard |
| GET | `/api/dashboard-stats` | No | Chart.js data feed |
| POST | `/auth/login` | No | Get JWT token |
| POST | `/api/process` | Yes | Ingest single log |
| POST | `/api/batch` | Yes | Ingest batch of logs |
| GET | `/api/export` | Yes | Role-based export |
| GET | `/stats` | No | Summary statistics |
| GET | `/export` | Yes | Format export (csv/json/html) |
| GET | `/format/<mode>` | No | Format recent logs |
| GET | `/logs/critical` | No | Critical logs |
| GET | `/logs/errors` | No | Error logs |
| GET | `/logs/by-risk` | No | Logs by risk level |
| GET | `/compliance/dashboard` | Yes | Compliance overview |
| GET | `/compliance/metrics` | Yes | Compliance scores |
| GET | `/compliance/rtbf-requests` | Yes | RtBF list |
| POST | `/compliance/rtbf-requests` | Yes | New RtBF request |
| GET/PUT | `/compliance/rtbf-requests/<id>` | Yes | RtBF detail/update |
| GET | `/compliance/consents` | Yes | Consent records |
| POST | `/compliance/consents` | Yes | Record consent |
| PUT | `/compliance/consents/<id>` | Yes | Update consent |
| POST | `/compliance/access-logs` | Yes | Log data access |
| GET | `/compliance/access-logs` | Yes | Access log list |
| GET | `/compliance/audit-logs` | Yes | Audit trail |
| GET/POST | `/compliance/violations` | Yes | Violations list/create |
| GET | `/compliance/checklist` | Yes | Compliance checklist |
| PUT | `/compliance/checklist/<id>` | Yes | Update checklist item |
| GET | `/compliance/scores` | Yes | GDPR + KVKK scores |
| GET | `/compliance/data-categories` | Yes | Data categories |

### 8.3 Authentication Reference

**API Key (header):**
```
X-API-KEY: local-api-key
```

**API Key (query param):**
```
GET /api/export?role=security&api_key=local-api-key
```

**JWT (obtain token):**
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}'
# → {"data":{"access_token":"eyJ..."},"status":"ok"}
```

**JWT (use token):**
```
Authorization: Bearer eyJ...
```

### 8.4 Export Format Reference

| Role | Format | Extension | Field Count | Level Filter |
|---|---|---|---|---|
| security | CSV | .csv | 9 | ERROR, CRITICAL |
| developer | JSON | .json | all | ERROR, WARNING, CRITICAL |
| admin | HTML | .html | 8 | all |
| auditor | JSON (dual) | .json | all | all |
| analyst | CSV | .csv | 9 | all |

---

*Report generated: June 3, 2026*  
*Stack version: middleware:latest, data-generator:latest*  
*Commit: 286cb8c*
