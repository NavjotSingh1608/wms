# Warehouse Management System (WMS)

A role-based mobile Warehouse Management System for pharmaceutical/manufacturing facilities. Tracks raw materials from receipt through quarantine, QC testing, approval, dispensing, and finished goods dispatch — with a full regulatory audit trail.

**Stack:** React Native (Expo SDK 54) + FastAPI (Python 3.12) + PostgreSQL 15 + Redis 7 + Celery 5

---

## Table of Contents

1. [Application Flow](#application-flow)
2. [Architecture](#architecture)
3. [User Roles & Permissions](#user-roles--permissions)
4. [Module Breakdown](#module-breakdown)
5. [Project Structure](#project-structure)
6. [Quick Start](#quick-start)
7. [API Endpoints](#api-endpoints)
8. [Database Schema](#database-schema)
9. [What's Implemented vs Remaining](#whats-implemented-vs-remaining)

---

## Application Flow

### Raw Material Lifecycle (end-to-end)

```
SUPPLIER DELIVERS MATERIAL
        │
        ▼
[WAREHOUSE_EXEC] ── Create GRN ──────────────────────────────────────
│  Enter: item code, batch, supplier, manufacturer, qty, dates       │
│  System: auto-generate GRN-YYYY-NNNN, status = QUARANTINE         │
│  System: generate QR label (encodes grn_id), stock ledger IN       │
│  Print quarantine label                                            │
└────────────────────────────────────────────────────────────────────┘
        │
        ▼  Status: QUARANTINE
[QC_EXEC] ── QC Sampling ────────────────────────────────────────────
│  Scan QR → enter A.R. Number (AR-YYYY-NNNN) + sample qty          │
│  System: sampler identity from JWT (not typed), server timestamp   │
│  System: status → UNDER_TEST, stock ledger updated                 │
└────────────────────────────────────────────────────────────────────┘
        │
        ▼  Status: UNDER_TEST
[QC_HEAD] ── QC Decision ────────────────────────────────────────────
│  ┌─ APPROVE ─── must set retesting_date (mandatory)                │
│  │              status → APPROVED, material_issue_allowed = true    │
│  │              material now available for dispensing               │
│  │                                                                 │
│  └─ REJECT ──── must give rejection_reason (mandatory)             │
│                 status → REJECTED, material blocked                 │
└────────────────────────────────────────────────────────────────────┘
        │
        ├──── APPROVED path ─────────────────────────────────────────
        │
        ▼
[WAREHOUSE_EXEC] ── Assign Rack Number ──────────────────────────────
│  Update rack location (e.g. A3-R2-S4) after approval               │
└────────────────────────────────────────────────────────────────────┘
        │
        ▼
[CELERY BEAT] ── Daily Retest Alert (08:00 UTC) ─────────────────────
│  If retesting_date <= today + 15 days:                             │
│    → In-app notification to QC + Warehouse users                   │
│    → Email alert via SES                                           │
└────────────────────────────────────────────────────────────────────┘
        │
        ├──── Retest due → [WH_EXEC] Initiate Retesting ────────────
        │     Status → QUARANTINE_RETESTING, issue blocked           │
        │     New QR label generated, cycle back through QC flow     │
        │                                                            │
        ├──── Grade Transfer (IP → BP/USP) ──────────────────────────
        │     [WH_EXEC] creates request → [QC_HEAD] approves        │
        │     Atomic: deduct IP stock, credit BP/USP stock           │
        │     New QR label, audit logged                             │
        │                                                            │
        ▼
[WAREHOUSE_EXEC] ── Dispense to Manufacturing ───────────────────────
│  System enforces FEFO (earliest expiry first), FIFO as tiebreaker  │
│  Cannot override batch selection — system picks automatically      │
│  Partial dispensing allowed — real-time balance update              │
│  If balance = 0 → status = FULLY_DISPENSED                         │
└────────────────────────────────────────────────────────────────────┘


### Finished Goods Flow

[PRODUCTION] ── Create FG Record + Shipper Label ────────────────────
        │
        ▼  Status: PENDING_QA_VERIFICATION
[QA_EXEC] ── Verify qty & quality ───────────────────────────────────
        │
        ▼  Status: QA_VERIFIED
[QA_HEAD] ── Final approval ─────────────────────────────────────────
        │         (or reject → back to Production)
        ▼  Status: QA_APPROVED
[WAREHOUSE_EXEC] ── Receive FG into stock ───────────────────────────
        │
        ▼  Status: WH_RECEIVED
[WAREHOUSE_EXEC] ── Dispatch ────────────────────────────────────────
        │
        ▼  Status: DISPATCHED
```

### QR Code Scan Flow

```
User opens app → taps Scan → camera opens
        │
        ▼
Camera reads QR → decodes "WMS:GRN:{uuid}"
        │
        ▼
App calls GET /api/v1/qr/scan/{grn_id} (public, no auth needed)
        │
        ▼
API returns all current data for that material:
  - Status-aware: different fields shown per status
  - QUARANTINE: basic GRN info
  - UNDER_TEST: + A.R. number, sampler, sample date
  - APPROVED: + approver, retesting date, rack
  - REJECTED: + rejection reason
  - After dispensing: + total dispensed, balance, last dispense info
```

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  MOBILE APP (React Native / Expo SDK 54)             │
│  iOS + Android — tested via Expo Go                  │
│  Expo Router │ React Native Paper │ TanStack Query   │
└───────────────────────┬──────────────────────────────┘
                        │ HTTPS
┌───────────────────────▼──────────────────────────────┐
│  FASTAPI (Python 3.12) + Uvicorn                     │
│  JWT Auth │ RBAC │ Pydantic Validation │ Async I/O   │
├──────────────────────────────────────────────────────┤
│  CELERY WORKER        │  CELERY BEAT                 │
│  Label generation     │  Daily retest/expiry alerts  │
│  Email dispatch       │  Cron at 08:00 UTC           │
├──────────────────────────────────────────────────────┤
│  PostgreSQL 15   │  Redis 7       │  S3 / Local FS   │
│  Primary DB      │  Sessions,     │  QR label PDFs   │
│  15 tables       │  Celery broker │                   │
└──────────────────────────────────────────────────────┘
```

All services run via **Docker Compose** locally. See [RUN_AND_DEPLOY.md](RUN_AND_DEPLOY.md) for setup.

---

## User Roles & Permissions

| Role | Department | Key Permissions |
|------|-----------|----------------|
| **WAREHOUSE_EXEC** | Warehouse | Create GRN, print labels, assign rack, dispense, initiate retesting, request grade transfer, receive/dispatch FG |
| **WAREHOUSE_HEAD** | Warehouse | All above + revise GRN, authorize label reprint, view audit trail |
| **QC_EXEC** | Quality Control | Add A.R. number, perform sampling, set Under Test |
| **QC_HEAD** | Quality Control | All above + approve/reject materials, set retesting date, execute grade change, view audit |
| **PRODUCTION** | Production | Create finished goods, generate shipper labels |
| **QA_EXEC** | Quality Assurance | QA verify/approve finished goods |
| **QA_HEAD** | Quality Assurance | All above + revise FG entry, view audit |
| **PURCHASE** | Purchase | View stock reports (read-only) |

**Total users: 8** (fixed, admin-seeded — no self-registration)

**Test credentials:** `warehouse@test.com` / `Test@1234`

---

## Module Breakdown

### 1. GRN & Quarantine
- Create Goods Receipt Note with material details
- Auto-generate GRN number (`GRN-2026-0042`)
- Auto-generate QR code label (PDF via WeasyPrint)
- Stock ledger entry on creation
- GRN revision by Warehouse Head (soft-delete + new linked record)

### 2. QC Sampling
- QC Executive scans QR → enters A.R. Number and sample qty
- Sampler identity captured from JWT (not manual input)
- Timestamp server-generated (tamper-proof)
- Status: QUARANTINE → UNDER_TEST

### 3. QC Decision
- QC Head approves (retesting date mandatory) or rejects (reason mandatory)
- Approval enables dispensing (`material_issue_allowed = true`)
- Rejection blocks all operations on the material

### 4. Retesting Management
- Daily Celery Beat job checks retesting dates (15-day threshold)
- Creates in-app notifications for QC + Warehouse users
- Warehouse initiates retesting → status back to QUARANTINE_RETESTING
- Full QC cycle repeats with incremented cycle number

### 5. Dispensing (FIFO/FEFO)
- Auto-selects batch by earliest expiry (FEFO), then earliest receipt (FIFO)
- Row-level DB lock prevents concurrent over-dispense
- Partial dispensing supported — balance updated in real-time
- Auto-transitions to FULLY_DISPENSED when balance = 0

### 6. Grade Transfer (IP → BP/USP)
- Warehouse requests transfer → QC Head approves
- Atomic transaction: deduct IP stock, credit BP/USP stock
- New GRN record + QR label for the transferred material
- Irreversible — corrections require new GRN

### 7. Finished Goods
- Production creates FG → QA verifies → QA Head approves
- Shipper label generation (barcode + product details)
- Warehouse receives and dispatches
- Full status lifecycle: PENDING_QA → QA_VERIFIED → QA_APPROVED → WH_RECEIVED → DISPATCHED

### 8. Stock Reports
- Stage-wise quantities: quarantine, under test, approved, rejected, dispensed
- Filterable by material, batch, A.R. number, status, date range
- CSV export for spreadsheet analysis

### 9. Audit Trail
- Every mutation logged: who, what, when, old values, new values
- Append-only table (no updates or deletes)
- Filterable by entity type, entity ID, user, date range
- 7-year retention per regulatory requirements

### 10. Notifications
- In-app notification centre with unread badge
- Retest alerts (15 days before due)
- Expiry alerts (30 days before expiry)
- Grade transfer requests, FG pending QA, label reprint requests

---

## Project Structure

```
wms/
├── backend/                         # FastAPI Python application
│   ├── app/
│   │   ├── main.py                  # App factory, 11 routers registered
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings (env vars)
│   │   │   ├── security.py          # JWT + bcrypt
│   │   │   ├── dependencies.py      # get_current_user, require_permission
│   │   │   └── database.py          # Async SQLAlchemy engine + session
│   │   ├── models/                  # 13 SQLAlchemy ORM models
│   │   │   ├── user.py              # User, Role, RefreshToken
│   │   │   ├── material.py          # Material master
│   │   │   ├── grn.py               # GRN + GRNStatus enum
│   │   │   ├── qc.py                # QCSampling, QCDecision
│   │   │   ├── dispensing.py        # Dispensing records
│   │   │   ├── stock_ledger.py      # Immutable transaction log
│   │   │   ├── qr_label.py          # QR label records
│   │   │   ├── retesting.py         # Retesting cycles
│   │   │   ├── grade_transfer.py    # Grade transfer records
│   │   │   ├── finished_goods.py    # FG + ShipperLabel
│   │   │   ├── notification.py      # In-app notifications
│   │   │   └── audit_log.py         # Audit trail (append-only)
│   │   ├── schemas/                 # 7 Pydantic schema files
│   │   ├── routers/                 # 11 FastAPI APIRouter files
│   │   │   ├── auth.py              # Login, refresh, logout, /me
│   │   │   ├── grn.py               # CRUD + revise + rack
│   │   │   ├── qc.py                # Sampling + decision
│   │   │   ├── dispensing.py        # Queue + dispense
│   │   │   ├── retesting.py         # Initiate + pending list
│   │   │   ├── grade_transfer.py    # Request + approve/reject
│   │   │   ├── finished_goods.py    # Full FG lifecycle
│   │   │   ├── qr.py                # Public QR scan endpoint
│   │   │   ├── reports.py           # Stock report + CSV export
│   │   │   ├── notifications.py     # List + mark read
│   │   │   └── audit.py             # Audit trail viewer
│   │   ├── services/                # 9 business logic files
│   │   ├── tasks/                   # Celery tasks (alerts, labels)
│   │   └── scripts/seed_db.py       # Seed roles, users, materials
│   ├── alembic/                     # DB migrations (2 versions)
│   ├── requirements.txt
│   └── Dockerfile
│
├── mobile/                          # React Native (Expo) app
│   ├── app/
│   │   ├── _layout.tsx              # Root: auth gate, QueryClient, Paper
│   │   ├── (auth)/login.tsx         # Login screen
│   │   ├── (app)/
│   │   │   ├── _layout.tsx          # Tab navigator (role-aware)
│   │   │   ├── dashboard.tsx        # Summary cards + quick actions
│   │   │   ├── grn/                 # List, Create, Detail [id]
│   │   │   ├── qc/                  # Pending list, Sampling, Decision
│   │   │   ├── dispensing/          # FEFO queue + dispense
│   │   │   ├── retesting/           # Pending retests
│   │   │   ├── grade-transfer/      # Request + approve/reject
│   │   │   ├── finished-goods/      # Full FG lifecycle
│   │   │   ├── reports/             # Stock report + export
│   │   │   ├── notifications/       # Notification centre
│   │   │   └── scan/scanner.tsx     # QR camera scanner
│   │   └── scan/[grn_id].tsx        # QR scan result (public)
│   ├── services/                    # 9 API wrapper files
│   ├── store/auth.ts                # Zustand auth state
│   ├── hooks/usePermission.ts       # Role/permission hooks
│   ├── components/                  # StatusBadge, EmptyState
│   └── constants/                   # API URL, Colors
│
├── docker-compose.yml               # API, Celery, PostgreSQL, Redis
├── .env.example                     # Env template
├── RUN_AND_DEPLOY.md                # Run/deploy guide
└── README.md                        # This file
```

---

## Quick Start

### Prerequisites
- **Docker Desktop** (for backend + database)
- **Node.js 18+** (for mobile app)
- **Expo Go** app on your phone

### 1. Start the backend
```powershell
cd E:\wms
copy .env.example .env.local           # Adjust if needed
docker compose up -d --build            # API + Celery + PostgreSQL + Redis
docker compose exec api alembic upgrade head    # Create all tables
docker compose exec api python -m app.scripts.seed_db  # Seed roles + users + materials
```

### 2. Verify
- http://localhost:8000/health → `{"status":"ok"}`
- http://localhost:8000/docs → Swagger UI with all 40+ endpoints

### 3. Start the mobile app
```powershell
cd E:\wms\mobile
npm install
npx expo start --clear
```
Scan the QR code with Expo Go. Login: `warehouse@test.com` / `Test@1234`

### Network note (phone on PC hotspot)
If your phone is on your PC's Mobile Hotspot:
```cmd
# Run as Administrator — forward Docker port to hotspot interface
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=192.168.137.1 connectport=8000 connectaddress=127.0.0.1
```
Update `mobile/.env`:
```
EXPO_PUBLIC_API_URL=http://192.168.137.1:8000/api/v1
```

---

## API Endpoints

| Method | Path | Auth | Permission | Description |
|--------|------|:----:|------------|-------------|
| `POST` | `/api/v1/auth/login` | - | - | Login → JWT tokens |
| `POST` | `/api/v1/auth/refresh` | - | - | Refresh access token |
| `POST` | `/api/v1/auth/logout` | Yes | - | Revoke refresh tokens |
| `GET` | `/api/v1/auth/me` | Yes | - | Current user info |
| `POST` | `/api/v1/grn` | Yes | `grn:create` | Create GRN |
| `GET` | `/api/v1/grn` | Yes | `stock:view` | List GRNs (paginated) |
| `GET` | `/api/v1/grn/{id}` | Yes | `stock:view` | GRN detail |
| `PUT` | `/api/v1/grn/{id}/rack` | Yes | `material:update_rack` | Update rack location |
| `POST` | `/api/v1/grn/{id}/revise` | Yes | `grn:revise` | Revise GRN (WH Head) |
| `POST` | `/api/v1/qc/sampling` | Yes | `qc:sampling` | Record QC sampling |
| `POST` | `/api/v1/qc/decision` | Yes | `qc:approve` | Approve or reject |
| `GET` | `/api/v1/dispensing/queue/{item_code}` | Yes | `material:issue` | FEFO queue |
| `POST` | `/api/v1/dispensing` | Yes | `material:issue` | Dispense material |
| `POST` | `/api/v1/retesting/initiate` | Yes | `retest:initiate` | Start retesting |
| `GET` | `/api/v1/retesting/pending` | Yes | `stock:view` | Pending retests |
| `POST` | `/api/v1/grade-transfers` | Yes | `grade:transfer_request` | Request transfer |
| `PUT` | `/api/v1/grade-transfers/{id}/approve` | Yes | `grade:change` | Approve transfer |
| `PUT` | `/api/v1/grade-transfers/{id}/reject` | Yes | `grade:change` | Reject transfer |
| `POST` | `/api/v1/fg` | Yes | `fg:send_to_warehouse` | Create FG record |
| `GET` | `/api/v1/fg` | Yes | `stock:view` | List FG records |
| `PUT` | `/api/v1/fg/{id}/qa-verify` | Yes | `fg:qa_approve` | QA verify FG |
| `PUT` | `/api/v1/fg/{id}/qa-approve` | Yes | `fg:qa_approve` | QA approve FG |
| `PUT` | `/api/v1/fg/{id}/qa-reject` | Yes | `fg:qa_approve` | QA reject FG |
| `PUT` | `/api/v1/fg/{id}/receive` | Yes | `fg:receive` | WH receive FG |
| `PUT` | `/api/v1/fg/{id}/dispatch` | Yes | `fg:dispatch` | Dispatch FG |
| `GET` | `/api/v1/qr/scan/{grn_id}` | **No** | - | Public QR scan |
| `GET` | `/api/v1/reports/stock` | Yes | `reports:view` | Stock report |
| `GET` | `/api/v1/reports/stock/export` | Yes | `reports:view` | CSV export |
| `GET` | `/api/v1/notifications` | Yes | - | List notifications |
| `PUT` | `/api/v1/notifications/{id}/read` | Yes | - | Mark as read |
| `GET` | `/api/v1/audit` | Yes | `audit:view` | Audit trail |
| `GET` | `/health` | - | - | Health check |

---

## Database Schema

**15 tables** across 2 Alembic migrations:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `roles` | 8 fixed roles with JSONB permissions | name, permissions[] |
| `users` | 8 users, JWT auth, lockout | email, password_hash, role_id |
| `refresh_tokens` | SHA-256 hashed refresh tokens | token_hash, expires_at |
| `materials` | Material master (item codes) | item_code (unique), item_name, grade |
| `grn` | Goods Receipt Notes | grn_number, status (8-value enum), balance_qty |
| `qc_sampling` | QC sample records | ar_number (unique), grn_id, sampled_by |
| `qc_decisions` | Approve/reject decisions | decision, retesting_date, rejection_reason |
| `dispensing` | Material issue records | grn_id, qty_issued, balance_qty_after |
| `stock_ledger` | Immutable transaction log | item_code, stage, txn_type, qty_change |
| `qr_labels` | QR code + PDF labels | grn_id, s3_key, is_current |
| `retesting_cycles` | Retest tracking | grn_id, cycle_no, outcome |
| `grade_transfers` | IP→BP/USP transfers | from/to item_code, status |
| `finished_goods` | FG lifecycle | status (6-value enum), qa/wh timestamps |
| `shipper_labels` | FG barcode labels | fg_id, barcode_data, s3_key |
| `notifications` | In-app alerts | user_id, type, is_read |
| `audit_log` | Append-only audit trail | entity_type, action, old/new values JSONB |

**9 PostgreSQL enums:** grn_status, qc_decision_type, ledger_txn_type, ledger_stage, label_type, retest_outcome, transfer_status, fg_status, notification_type

---

## What's Implemented vs Remaining

### Fully Implemented

| Area | Status |
|------|--------|
| Docker Compose (API, Celery, PostgreSQL, Redis) | Done |
| All 15 DB tables + migrations | Done |
| JWT authentication (login/refresh/logout/me) | Done |
| RBAC (require_permission dependency) | Done |
| GRN CRUD + revise + rack update | Done |
| QC sampling + decision (approve/reject) | Done |
| FEFO/FIFO dispensing with row-level locking | Done |
| Retesting management (initiate + alerts) | Done |
| Grade transfer (request + atomic approve) | Done |
| Finished goods full lifecycle | Done |
| Stock report (filterable + CSV export) | Done |
| Audit trail (append-only + viewer) | Done |
| Notifications (in-app + daily Celery alerts) | Done |
| Public QR scan endpoint | Done |
| Mobile: all 28 screens (auth, dashboard, GRN, QC, dispensing, FG, reports, notifications, QR scanner) | Done |
| Seed script (8 roles, test user, 4 materials) | Done |

### Remaining / Future Enhancements

| Item | Priority | Notes |
|------|----------|-------|
| **WeasyPrint PDF label generation** | High | Celery task exists but WeasyPrint needs system deps in Dockerfile (`libcairo2`, `libpango`). Add Jinja2 HTML template for A6 labels. |
| **S3 integration** | High | Currently label PDFs would store locally. Add boto3 S3 upload + pre-signed URLs for production. |
| **Email notifications (SES)** | Medium | Celery tasks log alerts but don't send emails yet. Add `boto3` SES integration in `email_service.py`. |
| **Expo push notifications** | Medium | Token storage in DB ready. Need to call Expo Push API from Celery alert tasks. |
| **Rate limiting** | Medium | Add `slowapi` middleware with Redis backend (100 req/min general, 10 req/min on login). |
| **All 8 user accounts seeded** | Low | Currently seeds 1 test user. Add remaining 7 users (one per role) to `seed_db.py`. |
| **Shipper label barcode generation** | Medium | Table exists. Add Code-128 barcode via `python-barcode` library. |
| **Audit middleware** | Low | Per-request audit logging (IP, user-agent). Currently audits are per-action in services. |
| **Unit/integration tests** | High | Add `pytest` + `httpx.AsyncClient` tests for all services and routes. |
| **CI/CD pipeline** | Medium | GitHub Actions: ruff → mypy → pytest → alembic check → deploy. |
| **EAS Build config** | Medium | Signed APK/IPA for staging/production distribution. |
| **Date pickers on mobile** | Low | GRN create and QC decision use `@react-native-community/datetimepicker`. Install if not already present. |
| **Offline mode** | Future | v1.0 is online-only. Offline queue + sync for v2. |
| **ERP integration** | Future | SAP/Oracle integration out of scope for v1.0. |
| **Multi-facility support** | Future | Single warehouse in v1.0. |

### To add WeasyPrint labels (highest priority remaining item):

```dockerfile
# Add to backend/Dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
```

```bash
# Add to requirements.txt
weasyprint>=61.0
jinja2>=3.1.0
qrcode[pil]>=7.4
```

Then implement `app/services/label_service.py` and `app/services/qr_service.py` to generate QR PNG → embed in HTML → render to A6 PDF via WeasyPrint.

---

## Full Technical Specification

The complete architecture document (HLD, LLD, API contract, DB schema, NFR, security, compliance, implementation phases) is in **WMS_README_v4.md**.
