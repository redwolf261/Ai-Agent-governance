# AI Agent Governance System
# Ethical AI Governance and Agent Task Auditing System

**Author:** Rivan Shetty  
**Group:** CS-K GRP 3  
**Roll No:** 13  
**PRN:** 12411956  

---

## 🎯 Project Overview

The AI Agent Governance System is a comprehensive platform for monitoring, controlling, and auditing AI agent activities. It provides:

- **Real-time Task Monitoring**: Track all AI agent tasks with detailed logging
- **Governance Rules Engine**: Define and enforce policies for AI behavior
- **ML-based Anomaly Detection**: Detect unusual or potentially harmful patterns
- **Audit Trail**: Complete compliance logging for accountability
- **Interactive Dashboard**: Visualize system status and manage approvals

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Navigate to the development directory:**
   ```bash
   cd 03_Development
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   ```bash
   python -c "from models.database import init_db; init_db()"
   ```

### Running the Application

**Start the server:**
```bash
python app.py
```

The server will start at `http://localhost:5000`

**Run the demo simulation:**
```bash
python demo_simulation.py
```

This will populate the system with sample data and demonstrate all features.

---

## 📁 Project Structure

```
03_Development/
├── app.py                    # Main application entry point
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── pytest.ini               # Test configuration
├── demo_simulation.py       # Demo/simulation script
│
├── models/                   # Database models
│   ├── __init__.py
│   ├── database.py          # SQLAlchemy setup
│   ├── agent.py             # AI Agent model
│   ├── task.py              # Task model
│   ├── audit_log.py         # Audit logging model
│   ├── governance_rule.py   # Governance rules model
│   └── user.py              # User authentication model
│
├── services/                 # Business logic layer
│   ├── __init__.py
│   ├── governance_engine.py # Rule evaluation engine
│   ├── anomaly_detector.py  # ML anomaly detection
│   ├── audit_service.py     # Audit logging service
│   ├── task_service.py      # Task management
│   └── agent_service.py     # Agent management
│
├── api/                      # REST API endpoints
│   ├── __init__.py
│   ├── routes.py            # Route registration
│   ├── agents.py            # Agent endpoints
│   ├── tasks.py             # Task endpoints
│   ├── governance.py        # Governance endpoints
│   ├── audit.py             # Audit endpoints
│   ├── dashboard.py         # Dashboard endpoints
│   └── auth.py              # Authentication endpoints
│
├── static/                   # Frontend assets
│   └── index.html           # Dashboard UI
│
└── tests/                    # Test suite
    └── test_all.py          # Unit and integration tests
```

---

## 🔧 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Authenticate user |
| GET | `/api/auth/me` | Get current user |

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents` | List all agents |
| POST | `/api/agents` | Register new agent |
| GET | `/api/agents/<id>` | Get agent details |
| POST | `/api/agents/<id>/suspend` | Suspend agent |
| POST | `/api/agents/<id>/activate` | Activate agent |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create task (with auto-evaluation) |
| GET | `/api/tasks/<id>` | Get task details |
| POST | `/api/tasks/<id>/approve` | Approve flagged task |
| POST | `/api/tasks/<id>/reject` | Reject flagged task |
| GET | `/api/tasks/flagged` | Get flagged tasks |

### Governance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/governance/rules` | List rules |
| POST | `/api/governance/rules` | Create rule |
| POST | `/api/governance/init-defaults` | Initialize defaults |

### Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit/logs` | Query audit logs |
| GET | `/api/audit/compliance-report` | Generate report |
| GET | `/api/audit/export` | Export logs (JSON/CSV) |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/summary` | Get summary stats |
| GET | `/api/dashboard/activity-timeline` | Activity over time |
| GET | `/api/dashboard/risk-overview` | Risk distribution |

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_all.py

# Run with coverage
pytest --cov=. --cov-report=html
```

---

## 📊 Features

### 1. Governance Rules Engine
- **Risk Threshold Rules**: Block tasks exceeding risk limits
- **Operation Restrictions**: Prevent dangerous operations
- **Task Type Restrictions**: Control allowed task types
- **Rate Limiting**: Prevent excessive task creation
- **Data Sensitivity**: Protect sensitive data access

### 2. ML Anomaly Detection
- **Isolation Forest**: Detects outlier task patterns
- **One-Class SVM**: Identifies normal behavior boundaries
- **Feature Extraction**: Analyzes 10+ task characteristics
- **Hybrid Scoring**: Combines rule-based and ML scores

### 3. Audit Logging
- **20+ Action Types**: Comprehensive event tracking
- **Severity Levels**: info, warning, error, critical
- **Compliance Reports**: Automated report generation
- **Export Formats**: JSON and CSV support

### 4. Dashboard UI
- **Real-time Statistics**: Active agents, tasks, violations
- **Activity Charts**: Timeline visualization
- **Risk Distribution**: Pie chart breakdown
- **Task Management**: Approve/reject flagged tasks
- **Rule Configuration**: Create and manage rules

---

## 🔐 Security Features

- JWT token-based authentication
- Bcrypt password hashing
- Role-based access control (Admin, Operator, Viewer)
- Audit trail for all operations
- CORS configuration for API security

---

## 📝 Configuration

Edit `config.py` to customize:

```python
# Database settings
database = DatabaseConfig(
    url="sqlite:///governance.db"  # Change for PostgreSQL
)

# Governance thresholds
governance = GovernanceConfig(
    risk_threshold=0.7,
    auto_block_threshold=0.9
)

# API settings
api = APIConfig(
    host="0.0.0.0",
    port=5000,
    debug=True
)
```

---

## 📈 Academic Deliverables

This project fulfills the following academic requirements:

1. ✅ Software Requirements Specification (SRS)
2. ✅ System Architecture Design
3. ✅ Database Schema Design
4. ✅ REST API Implementation
5. ✅ Machine Learning Integration
6. ✅ User Interface Dashboard
7. ✅ Unit and Integration Tests
8. ✅ Project Documentation
9. ✅ Demonstration Script

---

## 👨‍💻 Author

**Rivan Shetty**  
CS-K GRP 3 | Roll No: 13 | PRN: 12411956

---

## 📄 License

This project is submitted as part of academic coursework. All rights reserved.
