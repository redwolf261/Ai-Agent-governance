# Software Requirements Specification (SRS)
## Ethical AI Governance and Agent Task Auditing System

**Version:** 1.0  
**Date:** March 10, 2026  
**Prepared by:** Rivan Shetty  
**Group:** CS-K GRP 3 | Roll No: 13 | PRN: 12411956  
**Status:** Final  

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [System Constraints](#5-system-constraints)
6. [External Interface Requirements](#6-external-interface-requirements)
7. [Use Case Summary](#7-use-case-summary)

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) defines the functional and non-functional requirements for the **Ethical AI Governance and Agent Task Auditing System**. This document serves as the authoritative reference for development, testing, and acceptance of the system.

### 1.2 Scope
The system is a web-based platform that monitors, governs, and audits AI agents performing automated tasks in a software engineering environment. It enforces governance policies, detects anomalous behavior using machine learning, and maintains comprehensive audit trails for compliance purposes.

**In Scope:**
- AI agent registration and lifecycle management
- Task submission, execution tracking, and governance evaluation
- Rule-based policy enforcement engine
- ML-based anomaly detection (Isolation Forest, One-Class SVM)
- Real-time audit dashboard
- Compliance report generation
- Role-based access control (RBAC)

**Out of Scope:**
- AI agent implementation itself (agents are external entities)
- Cloud infrastructure provisioning
- Legal/regulatory compliance advice

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|-----------|
| AI Agent | An autonomous software component that executes tasks |
| Governance Rule | A policy definition that controls allowed agent behavior |
| Risk Score | A float (0.0–1.0) indicating anomaly likelihood of a task |
| Audit Log | An immutable record of every system event |
| RBAC | Role-Based Access Control |
| SRS | Software Requirements Specification |
| API | Application Programming Interface |
| JWT | JSON Web Token used for authentication |

### 1.4 References
- PROJECT_MASTER.md — Project overview and team structure
- `03_Development/models/` — Implemented data models
- `02_System_Design/USE_CASE_DIAGRAMS.md` — Use case documentation
- `06_Project_Management/Project_Plan.md` — Project timeline

### 1.5 Overview
Section 2 provides the product context. Section 3 details all functional requirements. Section 4 covers non-functional requirements. Section 5 defines constraints. Section 6 describes interfaces.

---

## 2. Overall Description

### 2.1 Product Perspective
The system is a standalone governance middleware layer. External AI agents communicate with it via REST API to register tasks. Administrators and auditors interact via the web dashboard.

```
[AI Agents] --> [REST API] --> [Governance Engine] --> [Database]
                                      |
                             [Anomaly Detector]
                                      |
                              [Audit Dashboard] <-- [Users/Auditors]
```

### 2.2 Product Features Summary

| # | Feature | Description |
|---|---------|-------------|
| F1 | Agent Management | Register, activate, suspend agents |
| F2 | Task Governance | Submit, evaluate, block/approve tasks |
| F3 | Anomaly Detection | ML scoring of tasks for risk |
| F4 | Audit Logging | Immutable logs of all events |
| F5 | rule Engine | Create and enforce governance policies |
| F6 | Dashboard | Real-time monitoring and visualization |
| F7 | Reporting | Generate compliance reports |
| F8 | Authentication | JWT-based RBAC system |

### 2.3 User Classes and Characteristics

| User Class | Description | Permissions |
|------------|-------------|-------------|
| **Admin** | Full system access, user management | All operations |
| **Auditor** | Reviews logs, generates reports | Read all, export reports |
| **Engineer** | Registers agents, submits tasks | Manage own agents/tasks |
| **Manager** | Oversees operations, views dashboard | Read all, approve/reject |
| **Viewer** | Observes system state | Read only |

### 2.4 Operating Environment
- **Backend:** Python 3.12, Flask, SQLAlchemy
- **Database:** SQLite (development), PostgreSQL (production)
- **ML Stack:** scikit-learn (Isolation Forest, One-Class SVM)
- **Frontend:** HTML5, JavaScript (static dashboard)
- **Auth:** JWT (PyJWT / Flask-JWT-Extended)
- **OS:** Linux/Windows server

### 2.5 Design and Implementation Constraints
- System must be deployable as a single Flask application
- Database schema must support full audit trail immutability
- ML models must be serializable (`.joblib`) for persistence
- All API responses must be JSON
- Passwords must be hashed using bcrypt

### 2.6 Assumptions and Dependencies
- AI agents are pre-existing and capable of making HTTP requests
- Python 3.10+ is available on the deployment server
- The ML models (`isolation_forest.joblib`, `one_class_svm.joblib`) are pre-trained and available

---

## 3. Functional Requirements

### 3.1 Authentication & Authorization Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AUTH-01 | The system SHALL allow users to register with username, email, password, and role | HIGH |
| FR-AUTH-02 | The system SHALL authenticate users via username/password and return a JWT token | HIGH |
| FR-AUTH-03 | The system SHALL validate JWT tokens on every protected API request | HIGH |
| FR-AUTH-04 | The system SHALL enforce role-based access control for all endpoints | HIGH |
| FR-AUTH-05 | The system SHALL hash all passwords using bcrypt before storage | HIGH |
| FR-AUTH-06 | The system SHALL invalidate tokens after 24 hours | MEDIUM |
| FR-AUTH-07 | The system SHALL log all login/logout events in the audit trail | MEDIUM |

### 3.2 Agent Management Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AGT-01 | The system SHALL allow registration of new AI agents with name, type, description, and capabilities | HIGH |
| FR-AGT-02 | The system SHALL support agent types: CODE_GENERATOR, CODE_REVIEWER, TEST_RUNNER, DOCUMENTATION, MONITORING, DEPLOYMENT, DATA_ANALYST, GENERAL | HIGH |
| FR-AGT-03 | The system SHALL assign one of the following statuses to agents: ACTIVE, INACTIVE, SUSPENDED, UNDER_REVIEW | HIGH |
| FR-AGT-04 | The system SHALL allow admin users to suspend or reactivate agents | HIGH |
| FR-AGT-05 | The system SHALL track the last active timestamp for each agent | MEDIUM |
| FR-AGT-06 | The system SHALL support marking agents as trusted, granting elevated permissions | MEDIUM |
| FR-AGT-07 | The system SHALL prevent SUSPENDED agents from submitting new tasks | HIGH |
| FR-AGT-08 | The system SHALL log all agent lifecycle events (registration, activation, suspension) | HIGH |

### 3.3 Task Governance Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-TSK-01 | The system SHALL accept task submissions with task_type, title, description, input_data, and agent_id | HIGH |
| FR-TSK-02 | The system SHALL support task types: CODE_GENERATION, CODE_REVIEW, TESTING, DOCUMENTATION, MONITORING, DEPLOYMENT, DATA_ANALYSIS, FILE_OPERATION, API_CALL, DATABASE_QUERY, SYSTEM_COMMAND | HIGH |
| FR-TSK-03 | The system SHALL evaluate every submitted task against all active governance rules | HIGH |
| FR-TSK-04 | The system SHALL assign task status: PENDING, RUNNING, COMPLETED, FAILED, BLOCKED, FLAGGED, APPROVED, REJECTED | HIGH |
| FR-TSK-05 | The system SHALL assign risk levels: LOW, MEDIUM, HIGH, CRITICAL | HIGH |
| FR-TSK-06 | The system SHALL store decision_rationale and governance_notes for every evaluated task | HIGH |
| FR-TSK-07 | The system SHALL record execution_time_ms for completed tasks | MEDIUM |
| FR-TSK-08 | The system SHALL allow admin/manager users to manually approve or reject flagged tasks | HIGH |
| FR-TSK-09 | The system SHALL block SUSPENDED agents from task submission | HIGH |

### 3.4 Governance Rules Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-RUL-01 | The system SHALL allow creation of governance rules with: name, type, action, severity, conditions, priority | HIGH |
| FR-RUL-02 | The system SHALL support rule types: TASK_TYPE_RESTRICTION, EXECUTION_TIME_LIMIT, RESOURCE_ACCESS, DATA_SENSITIVITY, OPERATION_RESTRICTION, RISK_THRESHOLD, AGENT_TRUST_LEVEL, TIME_BASED, RATE_LIMIT, COMPLIANCE | HIGH |
| FR-RUL-03 | The system SHALL support rule actions: ALLOW, BLOCK, FLAG, ESCALATE, LOG_ONLY, REQUIRE_APPROVAL | HIGH |
| FR-RUL-04 | The system SHALL support rule severities: LOW, MEDIUM, HIGH, CRITICAL | HIGH |
| FR-RUL-05 | The system SHALL evaluate rules in order of priority (highest first) | HIGH |
| FR-RUL-06 | The system SHALL allow rules to be activated or deactivated without deletion | MEDIUM |
| FR-RUL-07 | The system SHALL log every rule trigger event in the audit trail | HIGH |
| FR-RUL-08 | The system SHALL support rule versioning to track changes over time | LOW |

### 3.5 Anomaly Detection Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-ANO-01 | The system SHALL compute a risk_score (0.0–1.0) for every submitted task using ML models | HIGH |
| FR-ANO-02 | The system SHALL support Isolation Forest algorithm for anomaly detection | HIGH |
| FR-ANO-03 | The system SHALL support One-Class SVM algorithm for anomaly detection | HIGH |
| FR-ANO-04 | The system SHALL classify tasks as anomalous if risk_score exceeds a configurable threshold | HIGH |
| FR-ANO-05 | The system SHALL persist trained ML models as `.joblib` files | MEDIUM |
| FR-ANO-06 | The system SHALL extract features from task metadata for model input | HIGH |
| FR-ANO-07 | The system SHALL support model retraining with updated task data | LOW |

### 3.6 Audit Logging Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AUD-01 | The system SHALL log all task lifecycle events: CREATED, STARTED, COMPLETED, FAILED, FLAGGED, BLOCKED, APPROVED, REJECTED | HIGH |
| FR-AUD-02 | The system SHALL log all agent events: REGISTERED, ACTIVATED, SUSPENDED, UPDATED | HIGH |
| FR-AUD-03 | The system SHALL log all governance events: RULE_CREATED, RULE_UPDATED, RULE_DELETED, RULE_TRIGGERED | HIGH |
| FR-AUD-04 | The system SHALL log all user events: LOGIN, LOGOUT, ROLE_CHANGED | HIGH |
| FR-AUD-05 | The system SHALL make audit logs immutable — no update or delete operations permitted | HIGH |
| FR-AUD-06 | The system SHALL store actor_type, actor_id, timestamp, and details for every log entry | HIGH |
| FR-AUD-07 | The system SHALL support filtering audit logs by actor, action type, date range | MEDIUM |

### 3.7 Dashboard & Reporting Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-DSH-01 | The system SHALL provide a real-time dashboard showing agent statuses, task counts, and risk distribution | HIGH |
| FR-DSH-02 | The system SHALL display recent audit logs on the dashboard | HIGH |
| FR-DSH-03 | The system SHALL show governance rule violation statistics | MEDIUM |
| FR-DSH-04 | The system SHALL generate compliance audit reports on demand | HIGH |
| FR-DSH-05 | The system SHALL support export of reports in JSON format | MEDIUM |
| FR-DSH-06 | The system SHALL provide summary statistics: total agents, tasks by status, risk breakdown | HIGH |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement |
|----|-------------|
| NFR-PER-01 | Task logging latency SHALL be < 500ms under normal load |
| NFR-PER-02 | The system SHALL support ≥ 100 concurrent agent connections |
| NFR-PER-03 | Dashboard queries SHALL return within 2 seconds for up to 10,000 records |
| NFR-PER-04 | ML risk scoring SHALL complete within 200ms per task |

### 4.2 Reliability & Availability

| ID | Requirement |
|----|-------------|
| NFR-REL-01 | The system SHALL achieve 99% uptime during operational hours |
| NFR-REL-02 | The system SHALL recover from database failures within 30 seconds |
| NFR-REL-03 | Audit logs SHALL never be lost, even during system failure |

### 4.3 Security

| ID | Requirement |
|----|-------------|
| NFR-SEC-01 | All API endpoints (except /auth/login and /auth/register) SHALL require valid JWT token |
| NFR-SEC-02 | Passwords SHALL be hashed with bcrypt (cost factor ≥ 12) |
| NFR-SEC-03 | The system SHALL prevent SQL injection via ORM parameterized queries |
| NFR-SEC-04 | The system SHALL validate and sanitize all input data |
| NFR-SEC-05 | CORS SHALL be restricted to authorized origins in production |
| NFR-SEC-06 | The system SHALL log all unauthorized access attempts |

### 4.4 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-MNT-01 | Source code SHALL follow PEP 8 Python style guidelines |
| NFR-MNT-02 | All modules SHALL have unit test coverage ≥ 80% |
| NFR-MNT-03 | All public functions SHALL have docstrings |
| NFR-MNT-04 | Database migrations SHALL be managed via schema versioning |

### 4.5 Usability

| ID | Requirement |
|----|-------------|
| NFR-USE-01 | The dashboard SHALL be usable on Chrome, Firefox, and Edge browsers |
| NFR-USE-02 | API responses SHALL follow a consistent JSON schema |
| NFR-USE-03 | Error messages SHALL include descriptive human-readable text |

---

## 5. System Constraints

- **Technology:** Python 3.12, Flask, SQLAlchemy — no deviation without approval
- **Database:** SQLite for prototype; production migration to PostgreSQL planned
- **ML Models:** Pre-trained models must be version-controlled alongside source code
- **Deployment:** Single-server deployment; containerization (Docker) is a future scope item
- **Budget:** Development uses open-source tools exclusively
- **Timeline:** Phase 1 complete by end of Week 4; Phase 2 complete by end of Week 8

---

## 6. External Interface Requirements

### 6.1 User Interface
- Web dashboard served at `/` as a single HTML page
- Responsive layout supporting 1280x768 minimum resolution
- REST API documentation available via `/api/` endpoint

### 6.2 API Interface — Key Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Authenticate user, returns JWT | No |
| GET | `/api/agents/` | List all agents | Yes |
| POST | `/api/agents/` | Register new agent | Yes |
| PUT | `/api/agents/{id}/suspend` | Suspend agent | Admin |
| GET | `/api/tasks/` | List tasks | Yes |
| POST | `/api/tasks/` | Submit new task | Yes |
| PUT | `/api/tasks/{id}/approve` | Approve flagged task | Admin/Manager |
| GET | `/api/governance/rules` | List governance rules | Yes |
| POST | `/api/governance/rules` | Create governance rule | Admin |
| GET | `/api/audit/logs` | Retrieve audit logs | Auditor/Admin |
| GET | `/api/dashboard/summary` | Get dashboard stats | Yes |

### 6.3 Database Interface
- ORM: SQLAlchemy with declarative models
- Tables: `users`, `agents`, `tasks`, `audit_logs`, `governance_rules`
- All foreign keys enforce referential integrity
- Timestamps stored as UTC datetime

### 6.4 ML Model Interface
- Models loaded from `models/isolation_forest.joblib`, `models/one_class_svm.joblib`, `models/scaler.joblib`
- Input: feature vector (task_type, execution_time, risk_score components)
- Output: anomaly score (float), is_anomalous (boolean)

---

## 7. Use Case Summary

| Use Case | Actor | Description |
|----------|-------|-------------|
| UC-01 | Admin/Engineer | Register and manage AI agents |
| UC-02 | User | Authenticate via login |
| UC-03 | Agent/Engineer | Submit and track AI tasks |
| UC-04 | System | Evaluate tasks against governance rules |
| UC-05 | Admin | Create and manage governance rules |
| UC-06 | Auditor | View audit logs and generate reports |
| UC-07 | System | Detect anomalies with ML models |
| UC-08 | Admin/Manager | Advanced governance and escalation |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | Feb 4, 2026 | Rivan Shetty | Initial template |
| 1.0 | Mar 10, 2026 | Rivan Shetty | Full requirements populated |
