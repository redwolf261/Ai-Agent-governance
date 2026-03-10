# Statement of Work (SOW)
## Ethical AI Governance and Agent Task Auditing System

**Version:** 1.0  
**Date:** March 10, 2026  
**Prepared by:** Rivan Shetty  
**Group:** CS-K GRP 3 | Roll No: 13 | PRN: 12411956  

---

## 1. Project Overview

### 1.1 Project Title
**Ethical AI Governance and Agent Task Auditing System**

### 1.2 Project Purpose
This project designs and develops a governance platform that monitors, controls, and audits AI agents performing automated tasks in a software engineering environment. As AI agents become increasingly autonomous, the need for transparent oversight, policy enforcement, and anomaly detection is critical to responsible deployment.

### 1.3 Background
AI agents are being deployed across software development pipelines to perform tasks such as code generation, code review, testing, deployment, and data analysis. Without governance mechanisms, these agents may perform unauthorized actions, access sensitive data, or behave anomalously. This system addresses those risks through a structured governance, auditing, and anomaly detection platform.

---

## 2. Scope of Work

### 2.1 In Scope

| # | Deliverable | Description |
|---|-------------|-------------|
| D1 | Requirements Documentation | SOW, SRS, Requirement Traceability Matrix |
| D2 | System Design | UML diagrams (Use Case, Class, Object, Sequence, Activity, State, Deployment, Component) |
| D3 | Core Backend | Flask REST API with all modules implemented |
| D4 | Database Layer | SQLAlchemy ORM models for all entities |
| D5 | Governance Engine | Rule evaluation engine with priority-based processing |
| D6 | Anomaly Detection | ML-based risk scoring (Isolation Forest, One-Class SVM) |
| D7 | Audit Module | Immutable event logging system |
| D8 | Dashboard | Real-time web monitoring dashboard |
| D9 | Testing | Unit tests, integration tests, test reports |
| D10 | Final Documentation | System architecture doc, user guide, governance policies |
| D11 | Project Management | Project plan, risk register, cost estimation, progress tracking |

### 2.2 Out of Scope
- Development of the AI agents themselves (they are treated as external black-box clients)
- Cloud deployment infrastructure (AWS, Azure, GCP)
- Mobile application interface
- Legal compliance certification
- Real-time streaming data pipelines

---

## 3. Deliverables Schedule

| Deliverable | Phase | Due Date | Status |
|-------------|-------|----------|--------|
| SRS v1.0 | Phase 1 | Week 2 | ✅ Complete |
| SOW v1.0 | Phase 1 | Week 2 | ✅ Complete |
| System Architecture Design | Phase 1 | Week 3 | ✅ Complete |
| Use Case Diagrams (8) | Phase 1 | Week 3 | ✅ Complete |
| Class Diagram | Phase 1 | Week 4 | ✅ Complete |
| Object Diagram | Phase 1 | Week 4 | ✅ Complete |
| Sequence Diagrams | Phase 2 | Week 6 | ✅ Complete |
| Activity & State Diagrams | Phase 2 | Week 6 | ✅ Complete |
| Deployment & Component Diagrams | Phase 2 | Week 7 | ✅ Complete |
| Core Backend (all modules) | Phase 2 | Week 7 | ✅ Complete |
| ML Anomaly Detection | Phase 2 | Week 7 | ✅ Complete |
| Test Suite | Phase 2 | Week 8 | ✅ Complete |
| Requirement Traceability Matrix | Phase 2 | Week 8 | ✅ Complete |
| Final Documentation | Phase 3 | Week 12 | 🔄 In Progress |

---

## 4. Project Team

| Role | Name | Responsibilities |
|------|------|-----------------|
| **Project Lead / Full Stack Dev** | Rivan Shetty | Architecture, Backend, ML, Documentation |
| **Requirements Lead** | Rivan Shetty | SRS, SOW, RTM |
| **System Design Lead** | Rivan Shetty | UML diagrams, architecture design |
| **ML Lead** | Rivan Shetty | Anomaly detection models, risk scoring |
| **PM & QA Lead** | Rivan Shetty | Project plan, risk, testing |

---

## 5. Technical Approach

### 5.1 Architecture
The system follows a **layered architecture**:
1. **Presentation Layer** — Static HTML/JS dashboard, REST API
2. **Business Logic Layer** — Governance Engine, Anomaly Detector, Services
3. **Data Layer** — SQLAlchemy ORM, SQLite/PostgreSQL

### 5.2 Methodology
- **Development:** Iterative development with modular components
- **Design:** UML-first design approach with traceability to requirements
- **Testing:** Pytest-based unit and integration tests
- **Version Control:** Git with GitHub (`redwolf261/Ai-Agent-governance`)

### 5.3 Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| Web Framework | Flask |
| ORM | SQLAlchemy |
| Authentication | JWT (bcrypt) |
| ML Models | scikit-learn |
| Testing | pytest |
| Version Control | Git / GitHub |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Diagramming | Mermaid.js |

---

## 6. Assumptions

1. All AI agents communicate via HTTP REST API
2. The development environment has Python 3.10+ installed
3. Pre-trained ML models are available for initial deployment
4. A single developer handles all roles for this academic project
5. SQLite is acceptable for demonstration/academic purposes
6. No real production deployment is required during the project duration

---

## 7. Constraints

| Constraint | Description |
|------------|-------------|
| **Time** | 3-month project duration (Weeks 1–12) |
| **Budget** | Open-source tools only — zero cost |
| **Team** | Single developer (academic project) |
| **Stack** | Python/Flask mandated by project scope |
| **Scope** | Academic demonstration system, not production-grade |

---

## 8. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ML model accuracy insufficient | Medium | High | Use multiple algorithms, validate against test data |
| Time overrun on documentation | High | Medium | Use templates; generate diagrams programmatically |
| Scope creep | Medium | Medium | Strict scope definition in SOW; defer enhancements |
| Data availability for ML training | Low | High | Use synthetic/simulated task data |
| Integration failures | Low | Medium | Test each module independently before integration |

---

## 9. Acceptance Criteria

The project will be considered complete when:

1. ✅ All 11 deliverables are submitted
2. ✅ Unit test coverage ≥ 80%
3. ✅ All HIGH priority functional requirements are implemented
4. ✅ System successfully demonstrates: agent registration, task governance, anomaly detection, audit logging
5. ✅ All UML diagrams are complete and traceable to requirements
6. ✅ Final documentation package is submitted

---

## 10. Sign-off

| Role | Name | Date |
|------|------|------|
| Student / Developer | Rivan Shetty | March 10, 2026 |
| Group | CS-K GRP 3 | March 10, 2026 |
