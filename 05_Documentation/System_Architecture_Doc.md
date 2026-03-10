# System Architecture Document
## Ethical AI Governance and Agent Task Auditing System

**Version:** 1.0  
**Date:** March 10, 2026  
**Author:** Rivan Shetty | PRN: 12411956 | CS-K GRP 3  

---

## 1. Introduction

### 1.1 Purpose
This document describes the software architecture of the Ethical AI Governance and Agent Task Auditing System. It covers the architectural decisions, component breakdown, module interactions, and data design.

### 1.2 Scope
Covers the full backend system, ML pipeline, database schema, API design, and the static web dashboard.

---

## 2. Architectural Overview

The system follows a **four-layer architecture**:

```
┌────────────────────────────────────────────────────────┐
│                   CLIENT LAYER                         │
│   Web Browser (Dashboard)  |  AI Agent (HTTP Client)  │
└──────────────────┬─────────────────────────────────────┘
                   │ HTTP REST
┌──────────────────▼─────────────────────────────────────┐
│                   API LAYER (Flask)                    │
│  /api/auth | /api/agents | /api/tasks | /api/audit     │
│  /api/governance | /api/dashboard                      │
└──────────────────┬─────────────────────────────────────┘
                   │ Function calls
┌──────────────────▼─────────────────────────────────────┐
│               SERVICE / BUSINESS LOGIC LAYER           │
│  GovernanceEngine | AnomalyDetector | AuditService     │
│  AgentService | TaskService | AdvancedGovernanceRules  │
└──────────────────┬─────────────────────────────────────┘
                   │ SQLAlchemy ORM
┌──────────────────▼─────────────────────────────────────┐
│                   DATA LAYER                           │
│  SQLite / PostgreSQL  |  ML Model Store (.joblib)      │
└────────────────────────────────────────────────────────┘
```

---

## 3. Component Descriptions

### 3.1 API Layer

| Module | File | Responsibility |
|--------|------|----------------|
| Auth API | `api/auth.py` | User registration, login, JWT token issuance |
| Agents API | `api/agents.py` | Agent CRUD, suspend/activate, list |
| Tasks API | `api/tasks.py` | Task submission, approval, status updates |
| Governance API | `api/governance.py` | Rules CRUD, rule activation |
| Audit API | `api/audit.py` | Log retrieval, report generation |
| Dashboard API | `api/dashboard.py` | Summary stats, real-time status |
| Routes | `api/routes.py` | Blueprint registration with Flask app |

### 3.2 Service Layer

| Module | File | Responsibility |
|--------|------|----------------|
| GovernanceEngine | `services/governance_engine.py` | Evaluate tasks against all active rules, determine action |
| AnomalyDetector | `services/anomaly_detector.py` | Feature extraction, ML scoring (IF + SVM), risk classification |
| AuditService | `services/audit_service.py` | Create immutable audit log entries for all events |
| AgentService | `services/agent_service.py` | Business logic for agent lifecycle |
| TaskService | `services/task_service.py` | Task execution coordination, timing |
| AdvancedGovernanceRules | `services/advanced_governance_rules.py` | Complex rule evaluation (time-based, rate-limit, trust-level) |
| LlamaAgent | `services/llama_agent.py` | LLM-based agent for conversational governance |

### 3.3 Model Layer

| Model | File | DB Table | Key Fields |
|-------|------|----------|-----------|
| User | `models/user.py` | `users` | id, username, email, password_hash, role |
| Agent | `models/agent.py` | `agents` | id, name, agent_type, status, is_trusted, owner |
| Task | `models/task.py` | `tasks` | id, agent_id, task_type, status, risk_level, risk_score |
| GovernanceRule | `models/governance_rule.py` | `governance_rules` | id, name, type, action, severity, priority, is_active |
| AuditLog | `models/audit_log.py` | `audit_logs` | id, action, actor_type, actor_id, timestamp, details |
| Database | `models/database.py` | — | SQLAlchemy engine, session factory, Base |

---

## 4. Database Schema

### 4.1 Entity Relationship Summary

```
users ──────< tasks (via created_by FK)
agents ─────< tasks (via agent_id FK)
tasks ──────< audit_logs (via task_id FK)
agents ─────< audit_logs (via agent_id FK)
users ──────< audit_logs (via user_id FK)
governance_rules ─ evaluated against ─ tasks (in-memory, no direct FK)
```

### 4.2 Key Tables

**users**
```sql
id TEXT PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE,
password_hash TEXT, full_name TEXT, role TEXT, is_active BOOLEAN,
last_login DATETIME, created_at DATETIME
```

**agents**
```sql
id TEXT PRIMARY KEY, name TEXT UNIQUE, agent_type TEXT, description TEXT,
status TEXT, capabilities TEXT, created_at DATETIME, last_active_at DATETIME,
is_trusted BOOLEAN, owner TEXT, version TEXT
```

**tasks**
```sql
id TEXT PRIMARY KEY, agent_id TEXT FK(agents.id), task_type TEXT,
title TEXT, description TEXT, input_data TEXT, output_data TEXT,
status TEXT, risk_level TEXT, risk_score REAL, created_at DATETIME,
started_at DATETIME, completed_at DATETIME, execution_time_ms INTEGER,
decision_rationale TEXT, governance_status TEXT, governance_notes TEXT
```

**governance_rules**
```sql
id TEXT PRIMARY KEY, name TEXT UNIQUE, rule_type TEXT, description TEXT,
conditions TEXT, action TEXT, severity TEXT, priority INTEGER,
is_active BOOLEAN, created_at DATETIME, created_by TEXT
```

**audit_logs**
```sql
id TEXT PRIMARY KEY, action TEXT, actor_type TEXT, actor_id TEXT,
target_type TEXT, target_id TEXT, details TEXT, timestamp DATETIME,
ip_address TEXT, session_id TEXT
```

---

## 5. Security Architecture

### 5.1 Authentication Flow
1. User submits credentials to `POST /api/auth/login`
2. bcrypt verifies password against stored hash
3. JWT token generated with 24h expiry, signed with `SECRET_KEY`
4. Client stores token and includes in `Authorization: Bearer <token>` header
5. `@jwt_required` decorator validates token on every protected route

### 5.2 Authorization
- Role-based access control enforced at API layer
- Roles: ADMIN > MANAGER > AUDITOR > ENGINEER > VIEWER
- Decorators restrict endpoints: `@admin_required`, `@auditor_required`, etc.

### 5.3 Input Validation
- All request bodies validated for required fields before processing
- ORM parameterized queries prevent SQL injection
- No raw SQL strings in codebase

---

## 6. ML Architecture

### 6.1 Anomaly Detection Pipeline
```
Task Object
    │
    ▼
Feature Extraction (anomaly_detector.py)
[task_type_encoded, execution_time, risk_components, agent_trust_score]
    │
    ▼
StandardScaler (scaler.joblib) ── Normalize features
    │
    ├──▶ Isolation Forest (isolation_forest.joblib) ── Score 1
    └──▶ One-Class SVM (one_class_svm.joblib) ── Score 2
         │
         ▼
    Ensemble Score = weighted average
         │
         ▼
    Threshold (default: 0.5)
         │
    ├── < 0.4: LOW
    ├── 0.4–0.6: MEDIUM
    ├── 0.6–0.8: HIGH
    └── > 0.8: CRITICAL
```

### 6.2 Model Files
| File | Algorithm | Purpose |
|------|-----------|---------|
| `isolation_forest.joblib` | Isolation Forest | Primary anomaly scorer |
| `one_class_svm.joblib` | One-Class SVM | Secondary anomaly scorer |
| `scaler.joblib` | StandardScaler | Feature normalization |

---

## 7. Configuration

All configuration managed in `config.py` via environment variables:

| Config Key | Default | Description |
|------------|---------|-------------|
| `SECRET_KEY` | Random UUID | JWT signing key |
| `DATABASE_URL` | `sqlite:///ai_governance.db` | DB connection string |
| `DEBUG` | False | Flask debug mode |
| `JWT_EXPIRY_HOURS` | 24 | Token expiry |
| `ANOMALY_THRESHOLD` | 0.5 | ML decision boundary |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

---

## 8. Deployment Architecture

**Development:**
```
Local Machine → python app.py → http://localhost:5000
```

**Production (Target):**
```
AI Agents ─────┐
Web Browsers ──┼──▶ Nginx (Reverse Proxy :80/443)
                        │
                        ▼
               Flask App (Gunicorn :5000)
                        │
                        ▼
               PostgreSQL Database (:5432)
```

---

## 9. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Flask over Django | Lightweight, flexible; academic prototype needs minimal overhead |
| SQLite for dev | Zero-config, easily portable for academic demo |
| SQLAlchemy ORM | Abstracts DB, prevents SQL injection, supports migration to PostgreSQL |
| Joblib for ML | scikit-learn native serialization; fast load times |
| JWT for auth | Stateless; no server-side session storage needed |
| Mermaid.js for diagrams | Code-as-documentation; version-controllable |
| bcrypt for passwords | Industry standard; resistant to brute force |
