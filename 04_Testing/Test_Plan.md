# Test Plan
## Ethical AI Governance and Agent Task Auditing System

**Version:** 1.0  
**Date:** March 10, 2026  
**Author:** Rivan Shetty | PRN: 12411956  
**Group:** CS-K GRP 3  

---

## 1. Introduction

### 1.1 Purpose
This document defines the testing strategy, scope, approach, and schedule for the Ethical AI Governance and Agent Task Auditing System. It provides the framework for all testing activities ensuring the system meets requirements defined in the SRS.

### 1.2 Scope
Testing covers:
- All functional requirements (FR-AUTH, FR-AGT, FR-TSK, FR-RUL, FR-ANO, FR-AUD, FR-DSH)
- All REST API endpoints
- Database operations
- ML model integration
- Security controls (RBAC, JWT, input validation)

### 1.3 References
- `01_Requirements/SRS.md` — Functional requirements
- `01_Requirements/Requirement_Traceability_Matrix.md` — RTM
- `03_Development/tests/test_all.py` — Automated test suite

---

## 2. Test Strategy

### 2.1 Testing Levels

| Level | Description | Tools |
|-------|-------------|-------|
| **Unit Testing** | Test individual functions/methods in isolation | pytest, unittest.mock |
| **Integration Testing** | Test interactions between modules (API ↔ Service ↔ DB) | pytest, Flask test client |
| **System Testing** | End-to-end test of full workflows | pytest, manual |
| **Security Testing** | Test RBAC, JWT, SQL injection prevention | Manual + automated |
| **ML Model Testing** | Validate anomaly detection accuracy and output | pytest, sklearn metrics |

### 2.2 Test Approach
- **Automated:** All unit and integration tests via `pytest` in `03_Development/tests/`
- **Manual:** Dashboard UI testing via browser
- **Regression:** Run full test suite before every commit
- **Coverage Target:** ≥ 80% code coverage

### 2.3 Entry Criteria
- Source code committed to repository
- Development environment configured
- Test database initialized

### 2.4 Exit Criteria
- All HIGH priority test cases pass
- Code coverage ≥ 80%
- No CRITICAL or HIGH severity defects open
- All security test cases pass

---

## 3. Test Environment

| Component | Specification |
|-----------|--------------|
| OS | Windows 11 / Linux |
| Python | 3.12 |
| Framework | Flask (test client) |
| Database | SQLite (in-memory for tests) |
| Test Runner | pytest 7.x |
| Coverage | pytest-cov |
| Mocking | unittest.mock |

**Setup command:**
```bash
cd 03_Development
pip install -r requirements.txt
pytest tests/ -v --cov=. --cov-report=html
```

---

## 4. Test Cases

### 4.1 Authentication Module Tests

| TC ID | Test Case | Input | Expected Output | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-AUTH-01 | Register new user | {username, email, password, role} | 201 Created, user_id returned | HIGH |
| TC-AUTH-02 | Register duplicate username | Same username twice | 409 Conflict | HIGH |
| TC-AUTH-03 | Login with valid credentials | Correct username+password | 200 OK, JWT token returned | HIGH |
| TC-AUTH-04 | Login with wrong password | Wrong password | 401 Unauthorized | HIGH |
| TC-AUTH-05 | Access protected endpoint with valid JWT | Valid token in header | 200 OK | HIGH |
| TC-AUTH-06 | Access protected endpoint without token | No Authorization header | 401 Unauthorized | HIGH |
| TC-AUTH-07 | Access admin endpoint as viewer | Viewer JWT token | 403 Forbidden | HIGH |
| TC-AUTH-08 | Password stored as bcrypt hash | Register user, check DB | Raw password NOT in DB | HIGH |
| TC-AUTH-09 | Expired token rejected | Token > 24h old | 401 Unauthorized | MEDIUM |

### 4.2 Agent Management Tests

| TC ID | Test Case | Input | Expected Output | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-AGT-01 | Register new agent | {name, agent_type, description} | 201 Created, agent_id | HIGH |
| TC-AGT-02 | Register agent with duplicate name | Same name | 409 Conflict | HIGH |
| TC-AGT-03 | Get all agents | GET /api/agents/ | 200 OK, list of agents | HIGH |
| TC-AGT-04 | Suspend active agent | PUT /api/agents/{id}/suspend | 200 OK, status=SUSPENDED | HIGH |
| TC-AGT-05 | Suspended agent blocked from tasks | Suspended agent submits task | 403 Forbidden | HIGH |
| TC-AGT-06 | Reactivate suspended agent | PUT /api/agents/{id}/activate | 200 OK, status=ACTIVE | HIGH |
| TC-AGT-07 | Get agent by invalid ID | GET /api/agents/invalid-id | 404 Not Found | MEDIUM |
| TC-AGT-08 | Agent suspension logged in audit | Suspend agent | audit_log entry created | HIGH |

### 4.3 Task Governance Tests

| TC ID | Test Case | Input | Expected Output | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-TSK-01 | Submit valid task | {task_type, title, agent_id} | 201 Created, task_id | HIGH |
| TC-TSK-02 | Task auto-evaluated on submission | Submit task | governance_status set | HIGH |
| TC-TSK-03 | HIGH risk task flagged | Task with high risk_score | status=FLAGGED | HIGH |
| TC-TSK-04 | CRITICAL task blocked by rule | Deployment task with BLOCK rule | status=BLOCKED | HIGH |
| TC-TSK-05 | Approved task can be executed | Admin approves flagged task | status=APPROVED | HIGH |
| TC-TSK-06 | Rejected task cannot execute | Admin rejects task | status=REJECTED | HIGH |
| TC-TSK-07 | Task execution time recorded | Complete a task | execution_time_ms > 0 | MEDIUM |
| TC-TSK-08 | Decision rationale stored | Submit task | decision_rationale not null | HIGH |
| TC-TSK-09 | Task creation logged | Submit task | TASK_CREATED in audit_log | HIGH |
| TC-TSK-10 | Submit task for suspended agent | Suspended agent_id | 403 Forbidden | HIGH |

### 4.4 Governance Rules Tests

| TC ID | Test Case | Input | Expected Output | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-RUL-01 | Create governance rule | {name, type, action, severity} | 201 Created | HIGH |
| TC-RUL-02 | Rule applied on task submission | Active BLOCK rule, matching task | Task blocked | HIGH |
| TC-RUL-03 | Deactivated rule not applied | Deactivate rule, submit matching task | Task not blocked | HIGH |
| TC-RUL-04 | High priority rule evaluated first | Two conflicting rules | Higher priority wins | HIGH |
| TC-RUL-05 | Rule trigger logged | Rule triggers | RULE_TRIGGERED in audit_log | HIGH |
| TC-RUL-06 | Non-admin cannot create rules | Engineer tries to create rule | 403 Forbidden | HIGH |
| TC-RUL-07 | List all active rules | GET /api/governance/rules | 200 OK, rules list | MEDIUM |

### 4.5 Anomaly Detection Tests

| TC ID | Test Case | Input | Expected Output | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-ANO-01 | Risk score computed for every task | Submit any task | risk_score 0.0–1.0 | HIGH |
| TC-ANO-02 | Low risk task gets LOW level | Normal, routine task | risk_level=LOW | HIGH |
| TC-ANO-03 | Anomalous task gets HIGH/CRITICAL | Unusual task features | risk_level=HIGH or CRITICAL | HIGH |
| TC-ANO-04 | Isolation Forest model loads | App startup | No model load exception | HIGH |
| TC-ANO-05 | One-Class SVM model loads | App startup | No model load exception | HIGH |
| TC-ANO-06 | Feature extraction produces vector | Task object input | Float feature array output | HIGH |
| TC-ANO-07 | Score threshold classification | Score 0.85 | is_anomalous=True | HIGH |

### 4.6 Audit Logging Tests

| TC ID | Test Case | Input | Expected Output | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-AUD-01 | Task events produce audit logs | Create/complete/block task | Corresponding log entries | HIGH |
| TC-AUD-02 | Agent events produce audit logs | Register/suspend agent | Corresponding log entries | HIGH |
| TC-AUD-03 | Rule events produce audit logs | Create/delete rule | Corresponding log entries | HIGH |
| TC-AUD-04 | Audit logs are immutable | Try to update audit_log | 405 Method Not Allowed | HIGH |
| TC-AUD-05 | Filter logs by date range | GET /api/audit/logs?from=date | Filtered results | MEDIUM |
| TC-AUD-06 | Filter logs by actor | GET /api/audit/logs?actor_id=x | Actor-filtered results | MEDIUM |
| TC-AUD-07 | Audit log has all required fields | Check log record | actor_type, actor_id, timestamp, details present | HIGH |

### 4.7 Dashboard & Reporting Tests

| TC ID | Test Case | Input | Expected Output | Priority |
|-------|-----------|-------|-----------------|----------|
| TC-DSH-01 | Dashboard summary endpoint returns data | GET /api/dashboard/summary | 200 OK, stats object | HIGH |
| TC-DSH-02 | Task count by status in summary | Multiple tasks with statuses | Counts match reality | HIGH |
| TC-DSH-03 | Recent audit logs in dashboard | GET /api/dashboard/ | Last 10 log entries | MEDIUM |
| TC-DSH-04 | Generate compliance report | POST /api/audit/report/generate | Report with report_id | HIGH |
| TC-DSH-05 | Dashboard accessible without admin | Viewer role | 200 OK | MEDIUM |

---

## 5. Test Results Summary

Run tests with:
```bash
cd 03_Development
pytest tests/test_all.py -v --tb=short
```

Expected output file: `04_Testing/test_results.txt`

---

## 6. Defect Management

| Severity | Definition | Response Time |
|----------|-----------|---------------|
| **CRITICAL** | System crash, data loss, security breach | Fix immediately |
| **HIGH** | Feature broken, wrong results | Fix before release |
| **MEDIUM** | Feature partially working | Fix in next iteration |
| **LOW** | Minor UI or cosmetic issue | Fix if time permits |

---

## 7. Test Schedule

| Activity | Week | Owner |
|----------|------|-------|
| Unit test authoring | Week 5-6 | Rivan Shetty |
| Integration test authoring | Week 6-7 | Rivan Shetty |
| Test execution | Week 7-8 | Rivan Shetty |
| Security test execution | Week 8 | Rivan Shetty |
| Test report generation | Week 8 | Rivan Shetty |
| Regression testing | Week 9 | Rivan Shetty |
