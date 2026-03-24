# AI Agent Governance and Task Auditing System

A production-style governance platform for AI agents that combines policy rules, ML anomaly detection, auditability, and human-in-the-loop review.

Author: Rivan Shetty
Group: CS-K GRP 3
Roll No: 13
PRN: 12411956

---

## 1) What This Project Solves

Traditional AI safety checks focus on wrong answers. This project focuses on a harder real-world problem:

- agents can produce correct reasoning but still execute unsafe or unintended actions
- permission checks alone answer "can this be done?", not "should this be done now, in this context?"

This system intercepts agent tasks, scores risk, evaluates governance rules, decides allow or block or flag, and records every decision path for compliance.

---

## 2) Core Capabilities

### 2.1 Governance and Policy Enforcement

- Rule engine with priority-based evaluation
- Rule actions: allow, block, flag, escalate, log-only, require-approval
- Rule types include:
  - task type restriction
  - execution time limit
  - resource access checks
  - data sensitivity checks
  - operation restriction
  - risk threshold
  - agent trust level
  - time-based constraints
  - rate limiting
  - compliance rules
- Rule scope control:
  - all agents or selected agents
  - all task types or selected task types
- Versioning and active/inactive toggling

### 2.2 ML Risk and Anomaly Detection

- Isolation Forest + One-Class SVM ensemble
- Feature extraction from task and agent context
- Risk score in range 0.0 to 1.0
- Risk labels:
  - LOW
  - MEDIUM
  - HIGH
  - CRITICAL
- Model persistence using joblib artifacts in models/

### 2.3 Advanced Governance (Real-World Failure Modes)

Implemented in services/advanced_governance_rules.py:

- Boundary violations
- Goal misalignment
- Unsafe tool chaining
- Implicit norm violations
- Runaway behavior
- Security boundary violations

### 2.4 Audit and Compliance

- Full audit trail for user, agent, task, rule, and system actions
- 24 auditable action types (task, agent, governance, user, system)
- Filterable logs by date/action/entity/severity/actor
- Compliance report generation
- Export logs to JSON or CSV

### 2.5 Human-in-the-Loop Safety

- Flagged tasks require reviewer action
- Explicit approve/reject flow with reviewer notes
- Decision trace endpoint for explainability

### 2.6 Dashboard and Monitoring

- Summary metrics
- Activity timeline
- Agent performance and risk overview
- Governance trigger stats
- Live alerts feed

### 2.7 Optional Local LLM Integration

- Ollama-backed local Llama integration
- LLM-driven test scenario generation
- Governance testing against generated tasks

---

## 3) Architecture

### 3.1 High-Level Layered Architecture

1. API Layer (Flask blueprints)
2. Service Layer (business logic, governance, ML, auditing)
3. Model Layer (SQLAlchemy entities)
4. Persistence Layer (SQLite by default, PostgreSQL optional)
5. Presentation Layer (single-page dashboard in static/index.html)

### 3.2 Runtime Flow for Task Submission

1. Client calls POST /api/tasks
2. TaskService validates agent and payload
3. AnomalyDetector computes risk score and risk level
4. GovernanceEngine evaluates applicable rules by priority
5. Task status is set to approved/blocked/flagged/pending approval/escalated
6. AuditService records actions and rationale
7. Response returns task + evaluation payload

### 3.3 Project Structure

```text
Agent Governance/
├── 01_Requirements/
│   ├── SRS.md
│   ├── Requirement_Traceability_Matrix.md
│   └── SOW.md
├── 02_Documentation/
│   ├── ACADEMIC_JUSTIFICATION.md
│   ├── DATASET_JUSTIFICATION_AND_USAGE.md
│   └── VIVA_PREPARATION.md
├── 02_System_Design/
│   ├── OBJECT_DIAGRAM.md
│   ├── USE_CASE_DIAGRAMS.md
│   └── diagrams/
│       ├── uc01_overall.png
│       ├── uc02_authentication.png
│       ├── uc03_agent_management.png
│       ├── uc04_task_governance.png
│       ├── uc05_governance_rules.png
│       ├── uc06_audit_compliance.png
│       ├── uc07_ml_anomaly_detection.png
│       └── uc08_advanced_governance.png
├── 03_Development/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── static/
│   ├── tests/
│   ├── demo_simulation.py
│   ├── demo_adversarial.py
│   ├── demo_realworld_concerns.py
│   └── run_llama_tests.py
└── 04_Testing/
    ├── Test_Plan.md
    └── test_results.txt
```

---

## 4) Tech Stack

- Language: Python 3.12
- Framework: Flask 3.0.0
- ORM: SQLAlchemy 2.0
- DB: SQLite (default), PostgreSQL ready
- ML: scikit-learn (Isolation Forest, One-Class SVM), numpy, pandas
- Auth: JWT + bcrypt
- Config: python-dotenv
- Testing: pytest, pytest-cov, pytest-asyncio
- Optional LLM: Ollama + llama models

Full dependency list: requirements.txt

---

## 5) Data Model

### 5.1 Agent

- identity, type, status, trust flag, capability list, owner
- one-to-many with Task

### 5.2 Task

- type, status, risk_score, risk_level
- governance_status and notes
- execution timing and review metadata

### 5.3 GovernanceRule

- condition JSON + action + severity + priority
- versioning and activation lifecycle
- optional scope filters (agents/task types)

### 5.4 AuditLog

- action enum, timestamp, entity references
- severity and details payload

### 5.5 User

- role-based access model
- secure password hashing
- login metadata

---

## 6) Service Layer Responsibilities

### 6.1 GovernanceEngine

- loads applicable active rules
- evaluates conditions by rule type
- computes final governance decision
- logs triggered rule events

### 6.2 AnomalyDetector

- builds feature vectors
- applies ensemble model scoring
- maps score to LOW/MEDIUM/HIGH/CRITICAL

### 6.3 TaskService

- orchestrates create/start/complete/fail/review flows
- combines governance + anomaly outputs
- returns evaluation payloads for UI/API

### 6.4 AgentService

- registration and lifecycle operations
- trust level management
- per-agent statistics

### 6.5 AuditService

- centralized audit recording
- log querying, summaries, report generation, export

### 6.6 Advanced Governance Rules

- seeds practical safety rules for real-world agent risks

### 6.7 Llama Integration Service

- optional local LLM usage for testing and simulation

---

## 7) API Surface

Base URL: http://localhost:5000

### 7.1 Health and Discovery

- GET /health
- GET /api

### 7.2 Authentication

- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/logout
- POST /api/auth/change-password
- GET /api/auth/users (admin)
- PUT /api/auth/users/{user_id}/role (admin)

### 7.3 Agent Management

- GET /api/agents
- POST /api/agents
- GET /api/agents/{agent_id}
- PUT /api/agents/{agent_id}
- POST /api/agents/{agent_id}/suspend
- POST /api/agents/{agent_id}/activate
- POST /api/agents/{agent_id}/trust
- GET /api/agents/{agent_id}/statistics

### 7.4 Task Management

- GET /api/tasks
- POST /api/tasks
- GET /api/tasks/{task_id}
- POST /api/tasks/{task_id}/start
- POST /api/tasks/{task_id}/complete
- POST /api/tasks/{task_id}/fail
- POST /api/tasks/{task_id}/approve
- POST /api/tasks/{task_id}/reject
- GET /api/tasks/flagged
- GET /api/tasks/statistics
- GET /api/tasks/{task_id}/decision-trace

### 7.5 Governance

- GET /api/governance/rules
- GET /api/governance/rules/{rule_id}
- POST /api/governance/rules
- PUT /api/governance/rules/{rule_id}
- DELETE /api/governance/rules/{rule_id}
- POST /api/governance/rules/{rule_id}/toggle
- POST /api/governance/init-defaults
- GET /api/governance/rule-types

### 7.6 Audit

- GET /api/audit/logs
- GET /api/audit/task/{task_id}/trail
- GET /api/audit/agent/{agent_id}/trail
- GET /api/audit/compliance-report
- GET /api/audit/risk-summary
- GET /api/audit/export?format=json|csv
- GET /api/audit/actions

### 7.7 Dashboard

- GET /api/dashboard/summary
- GET /api/dashboard/activity-timeline
- GET /api/dashboard/agent-performance
- GET /api/dashboard/risk-overview
- GET /api/dashboard/recent-activity
- GET /api/dashboard/governance-stats
- GET /api/dashboard/live-alerts

---

## 8) Testing Conducted

### 8.1 Automated Test Suite

Primary file: tests/test_all.py

Coverage areas:

- Model behavior tests (Agent, Task)
- Governance engine tests (default rules, high-risk evaluation, priority ordering)
- Anomaly detector tests (training, feature extraction, risk score validity)
- API integration tests (health/docs, agent/task/rule/dashboard/audit endpoints)
- Service tests (AgentService, TaskService, AuditService)

Recorded result (from 04_Testing/test_results.txt):

- Collected tests: 34
- Passed: 34
- Failed: 0
- Runtime: ~13.86 seconds

### 8.2 Llama Integration Tests

File: tests/test_llama_integration.py

- Connection and model listing
- Generation and chat behavior
- Persona-based task generation
- Governance tester interactions
- Uses skip conditions when Ollama is unavailable

### 8.3 Test Plan and QA Artifacts

- Test strategy and cases: ../04_Testing/Test_Plan.md
- Execution output: ../04_Testing/test_results.txt

### 8.4 Security and Adversarial Validation

Adversarial scenarios in demo_adversarial.py:

- 10 attack simulations (database destruction, data exfiltration, backdoor deploy, monitoring disablement, financial manipulation, cryptomining, privilege escalation, ransomware, key harvesting, DDoS coordination)
- Script computes detection and block rates from runtime results

---

## 9) How to Recreate Locally from GitHub

### 9.1 Prerequisites

- Git
- Python 3.10+ (recommended 3.12)
- pip
- Optional: Ollama for Llama-based tests

### 9.2 Clone and Setup

```bash
# 1) Clone your repository
git clone <YOUR_GITHUB_REPO_URL>

# 2) Enter project root
cd "Agent Governance"

# 3) Enter application folder
cd 03_Development

# 4) Create virtual environment
python -m venv .venv

# 5) Activate environment
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

# 6) Install dependencies
pip install -r requirements.txt
```

### 9.3 Optional Environment Variables

Create a .env file in 03_Development if needed:

```env
# API
SECRET_KEY=change-this-in-real-deployments
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=true
JWT_EXPIRATION_HOURS=24

# Database (optional override)
DATABASE_URL=sqlite:///./ai_governance.db

# ML
ANOMALY_THRESHOLD=0.7
```

If .env is absent, sensible defaults from config.py are used.

### 9.4 Initialize Database and Start App

```bash
# initialize tables (safe to run multiple times)
python -c "from models.database import init_db; init_db()"

# run server
python app.py
```

Open:

- Dashboard: http://localhost:5000
- API docs summary: http://localhost:5000/api
- Health endpoint: http://localhost:5000/health

### 9.5 Run Tests

```bash
# all tests
pytest

# verbose
pytest -v

# specific suites
pytest tests/test_all.py -v --tb=short
pytest tests/test_llama_integration.py -v

# coverage
pytest --cov=. --cov-report=html
```

### 9.6 Run Demonstrations

```bash
# end-to-end simulation
python demo_simulation.py

# real-world governance concerns
python demo_realworld_concerns.py

# adversarial scenarios
python demo_adversarial.py
```

### 9.7 Optional: Enable Local Llama Tests (Ollama)

```bash
# install Ollama from https://ollama.ai
# then in terminal:
ollama serve
ollama pull llama3.2:latest

# run llama test script
python run_llama_tests.py
```

---

## 10) Deployment and Runtime Notes

- Default DB is local SQLite: ai_governance.db
- PostgreSQL is supported via DATABASE_URL/DatabaseConfig
- CORS is enabled for /api/*
- Time helper returns naive UTC timestamps for SQLAlchemy DateTime compatibility

---

## 11) Troubleshooting

### 11.1 Module or import issues

- ensure command is run from 03_Development
- ensure virtual environment is active
- reinstall dependencies: pip install -r requirements.txt

### 11.2 Database issues

```bash
python -c "from models.database import init_db; init_db()"
```

If schema drift occurs during local experimentation, remove ai_governance.db and re-run init_db.

### 11.3 Ollama unavailable

- start Ollama: ollama serve
- ensure endpoint responds: http://localhost:11434/api/tags
- Llama tests skip automatically when unavailable

### 11.4 Endpoint returns 401/403

- verify JWT token in Authorization header
- verify role for admin-only endpoints

---

## 12) Documentation Map

- Requirements:
  - ../01_Requirements/SRS.md
  - ../01_Requirements/Requirement_Traceability_Matrix.md
- System design:
  - ../02_System_Design/USE_CASE_DIAGRAMS.md
  - ../02_System_Design/OBJECT_DIAGRAM.md
  - ../02_System_Design/diagrams/
- Testing:
  - ../04_Testing/Test_Plan.md
  - ../04_Testing/test_results.txt
- Academic support:
  - ../02_Documentation/ACADEMIC_JUSTIFICATION.md
  - ../02_Documentation/DATASET_JUSTIFICATION_AND_USAGE.md
  - ../02_Documentation/VIVA_PREPARATION.md

---

## 13) License and Usage

This project was developed as academic coursework.

For portfolio or research reuse, retain attribution and review institutional policy before redistribution.
