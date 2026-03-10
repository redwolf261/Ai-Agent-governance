# Requirement Traceability Matrix (RTM)
## Ethical AI Governance and Agent Task Auditing System

**Version:** 1.0  
**Date:** March 10, 2026  
**Author:** Rivan Shetty | PRN: 12411956  

---

## Overview
This RTM maps every functional requirement to its corresponding design artifact, implementation file, test case, and verification status.

---

## Authentication Requirements

| Req ID | Requirement | Use Case | Design (UML) | Implementation | Test | Status |
|--------|-------------|----------|--------------|----------------|------|--------|
| FR-AUTH-01 | User registration | UC-02 | uc02_authentication.mmd | `api/auth.py` | `test_all.py::test_user_registration` | ✅ Done |
| FR-AUTH-02 | JWT login | UC-02 | uc02_authentication.mmd | `api/auth.py` | `test_all.py::test_login` | ✅ Done |
| FR-AUTH-03 | Token validation | UC-02 | Sequence Diagram SD-02 | `api/auth.py` | `test_all.py::test_protected_endpoint` | ✅ Done |
| FR-AUTH-04 | RBAC enforcement | UC-02 | uc02_authentication.mmd | `api/auth.py` | `test_all.py::test_rbac` | ✅ Done |
| FR-AUTH-05 | bcrypt password | UC-02 | — | `models/user.py` | `test_all.py::test_password_hash` | ✅ Done |
| FR-AUTH-06 | Token expiry 24h | UC-02 | — | `api/auth.py` | `test_all.py::test_token_expiry` | ✅ Done |
| FR-AUTH-07 | Log login events | UC-06 | uc06_audit_compliance.mmd | `services/audit_service.py` | `test_all.py::test_audit_login` | ✅ Done |

---

## Agent Management Requirements

| Req ID | Requirement | Use Case | Design (UML) | Implementation | Test | Status |
|--------|-------------|----------|--------------|----------------|------|--------|
| FR-AGT-01 | Register agents | UC-01 | uc03_agent_management.mmd | `api/agents.py` | `test_all.py::test_agent_registration` | ✅ Done |
| FR-AGT-02 | Agent types | UC-01 | class_diagram.mmd | `models/agent.py::AgentType` | `test_all.py::test_agent_types` | ✅ Done |
| FR-AGT-03 | Agent statuses | UC-01 | class_diagram.mmd | `models/agent.py::AgentStatus` | `test_all.py::test_agent_status` | ✅ Done |
| FR-AGT-04 | Suspend/activate | UC-01 | uc03_agent_management.mmd | `api/agents.py` | `test_all.py::test_suspend_agent` | ✅ Done |
| FR-AGT-05 | Last active timestamp | UC-01 | class_diagram.mmd | `models/agent.py` | `test_all.py::test_last_active` | ✅ Done |
| FR-AGT-06 | Trusted agent flag | UC-08 | uc08_advanced_governance.mmd | `models/agent.py` | `test_all.py::test_trusted_agent` | ✅ Done |
| FR-AGT-07 | Block suspended agents | UC-01 | uc03_agent_management.mmd | `services/agent_service.py` | `test_all.py::test_suspended_block` | ✅ Done |
| FR-AGT-08 | Log agent events | UC-06 | uc06_audit_compliance.mmd | `services/audit_service.py` | `test_all.py::test_agent_audit` | ✅ Done |

---

## Task Governance Requirements

| Req ID | Requirement | Use Case | Design (UML) | Implementation | Test | Status |
|--------|-------------|----------|--------------|----------------|------|--------|
| FR-TSK-01 | Accept task submissions | UC-03 | uc04_task_governance.mmd | `api/tasks.py` | `test_all.py::test_task_submission` | ✅ Done |
| FR-TSK-02 | Task types | UC-03 | class_diagram.mmd | `models/task.py::TaskType` | `test_all.py::test_task_types` | ✅ Done |
| FR-TSK-03 | Evaluate against rules | UC-04 | uc04_task_governance.mmd | `services/governance_engine.py` | `test_all.py::test_rule_evaluation` | ✅ Done |
| FR-TSK-04 | Task statuses | UC-03 | class_diagram.mmd | `models/task.py::TaskStatus` | `test_all.py::test_task_status` | ✅ Done |
| FR-TSK-05 | Risk level assignment | UC-07 | uc07_ml_anomaly_detection.mmd | `services/anomaly_detector.py` | `test_all.py::test_risk_level` | ✅ Done |
| FR-TSK-06 | Decision rationale stored | UC-04 | Sequence Diagram SD-03 | `models/task.py` | `test_all.py::test_decision_rationale` | ✅ Done |
| FR-TSK-07 | Execution time recorded | UC-03 | class_diagram.mmd | `services/task_service.py` | `test_all.py::test_exec_time` | ✅ Done |
| FR-TSK-08 | Manual approval | UC-08 | uc08_advanced_governance.mmd | `api/tasks.py` | `test_all.py::test_manual_approve` | ✅ Done |
| FR-TSK-09 | Block suspended agents | UC-03 | uc04_task_governance.mmd | `services/task_service.py` | `test_all.py::test_suspended_task_block` | ✅ Done |

---

## Governance Rules Requirements

| Req ID | Requirement | Use Case | Design (UML) | Implementation | Test | Status |
|--------|-------------|----------|--------------|----------------|------|--------|
| FR-RUL-01 | Create rules | UC-05 | uc05_governance_rules.mmd | `api/governance.py` | `test_all.py::test_create_rule` | ✅ Done |
| FR-RUL-02 | Rule types | UC-05 | class_diagram.mmd | `models/governance_rule.py::RuleType` | `test_all.py::test_rule_types` | ✅ Done |
| FR-RUL-03 | Rule actions | UC-05 | class_diagram.mmd | `models/governance_rule.py::RuleAction` | `test_all.py::test_rule_actions` | ✅ Done |
| FR-RUL-04 | Rule severities | UC-05 | class_diagram.mmd | `models/governance_rule.py::RuleSeverity` | `test_all.py::test_rule_severity` | ✅ Done |
| FR-RUL-05 | Priority ordering | UC-05 | uc05_governance_rules.mmd | `services/governance_engine.py` | `test_all.py::test_rule_priority` | ✅ Done |
| FR-RUL-06 | Activate/deactivate | UC-05 | uc05_governance_rules.mmd | `api/governance.py` | `test_all.py::test_rule_toggle` | ✅ Done |
| FR-RUL-07 | Log rule triggers | UC-06 | uc06_audit_compliance.mmd | `services/audit_service.py` | `test_all.py::test_rule_trigger_log` | ✅ Done |
| FR-RUL-08 | Rule versioning | UC-05 | — | `models/governance_rule.py` | — | ⏳ Partial |

---

## Anomaly Detection Requirements

| Req ID | Requirement | Use Case | Design (UML) | Implementation | Test | Status |
|--------|-------------|----------|--------------|----------------|------|--------|
| FR-ANO-01 | Risk score computation | UC-07 | uc07_ml_anomaly_detection.mmd | `services/anomaly_detector.py` | `test_all.py::test_risk_score` | ✅ Done |
| FR-ANO-02 | Isolation Forest | UC-07 | uc07_ml_anomaly_detection.mmd | `models/isolation_forest.joblib` | `test_all.py::test_isolation_forest` | ✅ Done |
| FR-ANO-03 | One-Class SVM | UC-07 | uc07_ml_anomaly_detection.mmd | `models/one_class_svm.joblib` | `test_all.py::test_svm` | ✅ Done |
| FR-ANO-04 | Threshold classification | UC-07 | uc07_ml_anomaly_detection.mmd | `services/anomaly_detector.py` | `test_all.py::test_threshold` | ✅ Done |
| FR-ANO-05 | Persist .joblib models | UC-07 | — | `models/*.joblib` | — | ✅ Done |
| FR-ANO-06 | Feature extraction | UC-07 | uc07_ml_anomaly_detection.mmd | `services/anomaly_detector.py` | `test_all.py::test_features` | ✅ Done |
| FR-ANO-07 | Model retraining | UC-07 | — | `services/anomaly_detector.py` | — | ⏳ Partial |

---

## Audit Logging Requirements

| Req ID | Requirement | Use Case | Design (UML) | Implementation | Test | Status |
|--------|-------------|----------|--------------|----------------|------|--------|
| FR-AUD-01 | Task event logging | UC-06 | uc06_audit_compliance.mmd | `services/audit_service.py` | `test_all.py::test_task_logs` | ✅ Done |
| FR-AUD-02 | Agent event logging | UC-06 | uc06_audit_compliance.mmd | `services/audit_service.py` | `test_all.py::test_agent_logs` | ✅ Done |
| FR-AUD-03 | Rule event logging | UC-06 | uc06_audit_compliance.mmd | `services/audit_service.py` | `test_all.py::test_rule_logs` | ✅ Done |
| FR-AUD-04 | User event logging | UC-06 | uc06_audit_compliance.mmd | `services/audit_service.py` | `test_all.py::test_user_logs` | ✅ Done |
| FR-AUD-05 | Immutable logs | UC-06 | uc06_audit_compliance.mmd | `models/audit_log.py` | `test_all.py::test_immutability` | ✅ Done |
| FR-AUD-06 | Log metadata stored | UC-06 | class_diagram.mmd | `models/audit_log.py` | `test_all.py::test_log_metadata` | ✅ Done |
| FR-AUD-07 | Log filtering | UC-06 | uc06_audit_compliance.mmd | `api/audit.py` | `test_all.py::test_log_filter` | ✅ Done |

---

## Dashboard & Reporting Requirements

| Req ID | Requirement | Use Case | Design (UML) | Implementation | Test | Status |
|--------|-------------|----------|--------------|----------------|------|--------|
| FR-DSH-01 | Real-time dashboard | UC-04 | Deployment Diagram | `api/dashboard.py` | `test_all.py::test_dashboard` | ✅ Done |
| FR-DSH-02 | Recent audit logs | UC-06 | — | `api/dashboard.py` | `test_all.py::test_dashboard_logs` | ✅ Done |
| FR-DSH-03 | Rule violation stats | UC-05 | — | `api/dashboard.py` | — | ⏳ Partial |
| FR-DSH-04 | Compliance reports | UC-06 | uc06_audit_compliance.mmd | `api/audit.py` | `test_all.py::test_report` | ✅ Done |
| FR-DSH-05 | JSON export | UC-06 | — | `api/audit.py` | — | ✅ Done |
| FR-DSH-06 | Summary statistics | UC-04 | — | `api/dashboard.py` | `test_all.py::test_summary` | ✅ Done |

---

## Coverage Summary

| Module | Total Reqs | Implemented | Partial | Not Started |
|--------|-----------|-------------|---------|-------------|
| Authentication | 7 | 7 | 0 | 0 |
| Agent Management | 8 | 8 | 0 | 0 |
| Task Governance | 9 | 9 | 0 | 0 |
| Governance Rules | 8 | 7 | 1 | 0 |
| Anomaly Detection | 7 | 6 | 1 | 0 |
| Audit Logging | 7 | 7 | 0 | 0 |
| Dashboard & Reporting | 6 | 5 | 1 | 0 |
| **Total** | **52** | **49** | **3** | **0** |
| **Coverage** | | **94%** | **6%** | **0%** |
