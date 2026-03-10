# User Guide
## Ethical AI Governance and Agent Task Auditing System

**Version:** 1.0  
**Date:** March 10, 2026  
**Author:** Rivan Shetty | CS-K GRP 3  

---

## 1. Getting Started

### 1.1 Prerequisites
- Python 3.10 or higher
- pip package manager
- Git

### 1.2 Installation

```bash
# 1. Clone the repository
git clone https://github.com/redwolf261/Ai-Agent-governance.git
cd "Ai-Agent-governance/03_Development"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python app.py
```

The server starts at **http://localhost:5000**

### 1.3 Access the Dashboard
Open your browser and navigate to: `http://localhost:5000`

---

## 2. User Roles & Permissions

| Role | What You Can Do |
|------|----------------|
| **Admin** | Everything: manage users, agents, rules, view all data |
| **Manager** | Approve/reject flagged tasks, view all data |
| **Auditor** | View all logs, generate compliance reports |
| **Engineer** | Register agents, submit tasks, view own data |
| **Viewer** | Read-only access to dashboard |

---

## 3. Core Workflows

### 3.1 Registering a User
**Endpoint:** `POST /api/auth/register`
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe",
  "role": "engineer"
}
```

### 3.2 Logging In
**Endpoint:** `POST /api/auth/login`
```json
{ "username": "john_doe", "password": "SecurePass123" }
```
**Response:** Returns JWT token — include in all subsequent requests:
```
Authorization: Bearer <your_token_here>
```

### 3.3 Registering an AI Agent
**Endpoint:** `POST /api/agents/`
```json
{
  "name": "CodeBot-v1",
  "agent_type": "code_generator",
  "description": "Generates Python code",
  "capabilities": ["python", "api_design"]
}
```

### 3.4 Submitting a Task
**Endpoint:** `POST /api/tasks/`
```json
{
  "agent_id": "<agent_uuid>",
  "task_type": "code_generation",
  "title": "Generate user authentication module",
  "description": "Create JWT auth for Flask app",
  "input_data": {"language": "python", "framework": "flask"}
}
```

**Possible responses:**
- `status: approved` — Task passed all governance checks
- `status: flagged` — Requires manual review
- `status: blocked` — Violated a governance rule

### 3.5 Creating a Governance Rule (Admin)
**Endpoint:** `POST /api/governance/rules`
```json
{
  "name": "Block Production Deployments",
  "rule_type": "task_type_restriction",
  "action": "block",
  "severity": "critical",
  "priority": 10,
  "conditions": {"task_type": "deployment"},
  "description": "Block all deployment tasks pending review"
}
```

### 3.6 Viewing Audit Logs
**Endpoint:** `GET /api/audit/logs`

Optional filters:
- `?action=TASK_BLOCKED` — Filter by action
- `?actor_id=<agent_id>` — Filter by actor
- `?from=2026-03-01&to=2026-03-10` — Date range

### 3.7 Generating a Report
**Endpoint:** `POST /api/audit/report/generate`

Returns a compliance report with task statistics, violations, and agent activity.

### 3.8 Approving a Flagged Task (Admin/Manager)
**Endpoint:** `PUT /api/tasks/<task_id>/approve`

### 3.9 Suspending an Agent (Admin)
**Endpoint:** `PUT /api/agents/<agent_id>/suspend`

---

## 4. Running Demo Scripts

The project includes demo scripts for testing:

```bash
# Run basic system simulation
python demo_simulation.py

# Run adversarial scenarios (tests blocking/flagging)
python demo_adversarial.py

# Run real-world governance concerns demo
python demo_realworld_concerns.py
```

---

## 5. Running Tests

```bash
cd 03_Development
pytest tests/test_all.py -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=html
```

---

## 6. API Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/agents/` | List agents |
| POST | `/api/agents/` | Register agent |
| GET | `/api/tasks/` | List tasks |
| POST | `/api/tasks/` | Submit task |
| GET | `/api/governance/rules` | List rules |
| POST | `/api/governance/rules` | Create rule |
| GET | `/api/audit/logs` | View audit logs |
| GET | `/api/dashboard/summary` | Dashboard stats |
| GET | `/health` | Health check |

---

## 7. Troubleshooting

| Issue | Solution |
|-------|----------|
| `401 Unauthorized` | Ensure JWT token is in the Authorization header |
| `403 Forbidden` | Your role doesn't have permission for this action |
| `Task blocked` | A governance rule is blocking the task — check `/api/governance/rules` |
| `Agent suspended error` | Reactivate the agent via `PUT /api/agents/{id}/activate` |
| Model load error | Ensure `.joblib` files exist in `models/` directory |
