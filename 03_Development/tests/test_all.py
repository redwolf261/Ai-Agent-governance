"""Aligned unit and integration tests for the current codebase."""

import json
import os
import sys

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.agent import Agent, AgentStatus, AgentType
from models.audit_log import AuditAction
from models.database import Base, engine, get_session
from models.governance_rule import GovernanceRule, RuleAction, RuleType
from models.task import RiskLevel, Task, TaskStatus, TaskType
from services.agent_service import AgentService
from services.anomaly_detector import AnomalyDetector
from services.audit_service import AuditService
from services.governance_engine import GovernanceEngine
from services.task_service import TaskService


@pytest.fixture(autouse=True)
def reset_database():
    """Reset the SQLite database before each test for deterministic runs."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session():
    db_session = get_session()
    try:
        yield db_session
    finally:
        db_session.close()


@pytest.fixture
def sample_agent(session):
    agent = Agent(
        name="Test Agent",
        agent_type=AgentType.CODE_GENERATOR,
        description="Test agent for unit tests",
        is_trusted=False,
    )
    session.add(agent)
    session.commit()
    return agent


@pytest.fixture
def sample_task(session, sample_agent):
    task = Task(
        agent_id=sample_agent.id,
        task_type=TaskType.CODE_GENERATION,
        title="Test Task",
        description="Test task for unit tests",
        input_data=json.dumps({"test": True}),
    )
    session.add(task)
    session.commit()
    return task


@pytest.fixture
def governance_engine(session):
    return GovernanceEngine(session)


@pytest.fixture
def anomaly_detector(tmp_path):
    detector = AnomalyDetector(model_path=str(tmp_path))
    training_data = detector.generate_synthetic_training_data(100)
    detector.train_models(training_data, contamination=0.1)
    return detector


class TestAgentModel:
    def test_agent_creation(self, session):
        agent = Agent(
            name="New Agent",
            agent_type=AgentType.CODE_REVIEWER,
            description="A code reviewing agent",
        )
        session.add(agent)
        session.commit()

        assert agent.id is not None
        assert agent.name == "New Agent"
        assert agent.agent_type == AgentType.CODE_REVIEWER
        assert agent.status == AgentStatus.ACTIVE
        assert agent.is_trusted is False

    def test_agent_update_last_active(self, session, sample_agent):
        sample_agent.update_last_active()
        session.commit()

        assert sample_agent.last_active_at is not None

    def test_agent_suspend_and_activate(self, session, sample_agent):
        sample_agent.suspend()
        session.commit()
        assert sample_agent.status == AgentStatus.SUSPENDED

        sample_agent.activate()
        session.commit()
        assert sample_agent.status == AgentStatus.ACTIVE

    def test_agent_to_dict(self, sample_agent):
        data = sample_agent.to_dict()

        assert data["name"] == "Test Agent"
        assert data["agent_type"] == "code_generator"
        assert data["is_trusted"] is False


class TestTaskModel:
    def test_task_creation(self, session, sample_agent):
        task = Task(
            agent_id=sample_agent.id,
            task_type=TaskType.DATA_ANALYSIS,
            title="Analysis Task",
            description="Analyze some data",
        )
        session.add(task)
        session.commit()

        assert task.id is not None
        assert task.status == TaskStatus.PENDING
        assert task.risk_score == 0.0
        assert task.governance_status == "pending"

    def test_task_start_execution(self, session, sample_task):
        sample_task.start_execution()
        session.commit()

        assert sample_task.status == TaskStatus.RUNNING
        assert sample_task.started_at is not None

    def test_task_complete_execution(self, session, sample_task):
        sample_task.start_execution()
        sample_task.complete_execution(json.dumps({"result": "success"}))
        session.commit()

        assert sample_task.status == TaskStatus.COMPLETED
        assert sample_task.completed_at is not None
        assert json.loads(sample_task.output_data)["result"] == "success"

    def test_task_fail_execution(self, session, sample_task):
        sample_task.start_execution()
        sample_task.fail_execution("Something went wrong")
        session.commit()

        assert sample_task.status == TaskStatus.FAILED
        assert "Something went wrong" in sample_task.output_data

    def test_task_flag_for_review(self, session, sample_task):
        sample_task.flag_for_review("High risk operation detected")
        session.commit()

        assert sample_task.status == TaskStatus.FLAGGED
        assert sample_task.governance_status == "flagged"
        assert "High risk operation detected" in sample_task.governance_notes

    def test_task_block_execution(self, session, sample_task):
        sample_task.block_execution("Violation: Restricted operation")
        session.commit()

        assert sample_task.status == TaskStatus.BLOCKED
        assert sample_task.governance_status == "blocked"

    def test_task_approve(self, session, sample_task):
        sample_task.flag_for_review("Needs review")
        sample_task.approve("reviewer-1", "Approved after review")
        session.commit()

        assert sample_task.status == TaskStatus.APPROVED
        assert sample_task.reviewed_by == "reviewer-1"


class TestGovernanceEngine:
    def test_create_default_rules(self, session, governance_engine):
        rules = governance_engine.create_default_rules()
        assert len(rules) >= 5

    def test_evaluate_low_risk_task(self, session, governance_engine, sample_task, sample_agent):
        governance_engine.create_default_rules()
        sample_task.task_type = TaskType.DOCUMENTATION
        sample_task.input_data = json.dumps({"estimated_execution_time": 60})
        sample_task.risk_score = 0.2
        session.commit()

        status, triggered_rules = governance_engine.evaluate_task(sample_task, sample_agent)

        assert status in ["approved", "flagged", "blocked", "pending_approval", "escalated"]
        assert isinstance(triggered_rules, list)

    def test_evaluate_high_risk_task(self, session, governance_engine, sample_task, sample_agent):
        governance_engine.create_default_rules()
        sample_task.task_type = TaskType.SYSTEM_COMMAND
        sample_task.input_data = json.dumps(
            {
                "operation": "credential_access",
                "estimated_execution_time": 7200,
            }
        )
        sample_task.description = "Access production password store"
        sample_task.risk_score = 0.95
        session.commit()

        status, triggered_rules = governance_engine.evaluate_task(sample_task, sample_agent)

        assert status in ["blocked", "flagged"]
        assert len(triggered_rules) > 0

    def test_rule_priority_orders_lowest_first(self, session, governance_engine, sample_task, sample_agent):
        session.add_all(
            [
                GovernanceRule(
                    name="Priority 50",
                    rule_type=RuleType.RISK_THRESHOLD,
                    condition=json.dumps({"threshold": 0.5}),
                    action=RuleAction.FLAG,
                    priority=50,
                ),
                GovernanceRule(
                    name="Priority 5",
                    rule_type=RuleType.RISK_THRESHOLD,
                    condition=json.dumps({"threshold": 0.9}),
                    action=RuleAction.BLOCK,
                    priority=5,
                ),
            ]
        )
        session.commit()

        rules = governance_engine._get_applicable_rules(sample_task, sample_agent)
        assert rules[0].priority <= rules[-1].priority


class TestAnomalyDetector:
    def test_training(self, tmp_path):
        detector = AnomalyDetector(model_path=str(tmp_path))
        training_data = detector.generate_synthetic_training_data(50)
        detector.train_models(training_data, contamination=0.1)

        assert detector.isolation_forest is not None
        assert detector.one_class_svm is not None
        assert detector.scaler is not None

    def test_feature_extraction(self, anomaly_detector, sample_task, sample_agent):
        features = anomaly_detector.extract_features(sample_task, sample_agent)

        assert features is not None
        assert features.shape == (1, 10)

    def test_risk_score_output(self, anomaly_detector, sample_task, sample_agent):
        score, level, analysis = anomaly_detector.calculate_risk_score(sample_task, sample_agent)

        assert 0 <= score <= 1
        assert level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert "final_score" in analysis


class TestAPIEndpoints:
    def test_health_check(self, client):
        response = client.get("/health")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["status"] == "healthy"

    def test_api_docs(self, client):
        response = client.get("/api")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert "endpoints" in data

    def test_register_agent_and_list_agents(self, client):
        create_response = client.post(
            "/api/agents",
            data=json.dumps(
                {
                    "name": "API Test Agent",
                    "agent_type": "code_generator",
                    "description": "Created via API test",
                }
            ),
            content_type="application/json",
        )
        create_data = json.loads(create_response.data)

        list_response = client.get("/api/agents")
        list_data = json.loads(list_response.data)

        assert create_response.status_code == 201
        assert create_data["success"] is True
        assert list_response.status_code == 200
        assert list_data["count"] >= 1

    def test_create_task_and_list_tasks(self, client):
        agent_response = client.post(
            "/api/agents",
            data=json.dumps(
                {
                    "name": "Task API Agent",
                    "agent_type": "documentation",
                    "description": "Agent for task API test",
                }
            ),
            content_type="application/json",
        )
        agent_id = json.loads(agent_response.data)["data"]["id"]

        task_response = client.post(
            "/api/tasks",
            data=json.dumps(
                {
                    "agent_id": agent_id,
                    "task_type": "documentation",
                    "title": "API Test Task",
                    "description": "Created through API",
                    "input_data": {"estimated_execution_time": 60},
                }
            ),
            content_type="application/json",
        )
        task_data = json.loads(task_response.data)

        list_response = client.get("/api/tasks")
        list_data = json.loads(list_response.data)

        assert task_response.status_code == 201
        assert task_data["success"] is True
        assert "evaluation" in task_data
        assert list_response.status_code == 200
        assert list_data["count"] >= 1

    def test_get_task_decision_trace(self, client):
        agent_response = client.post(
            "/api/agents",
            data=json.dumps(
                {
                    "name": "Trace API Agent",
                    "agent_type": "documentation",
                    "description": "Agent for trace endpoint test",
                }
            ),
            content_type="application/json",
        )
        agent_id = json.loads(agent_response.data)["data"]["id"]

        task_response = client.post(
            "/api/tasks",
            data=json.dumps(
                {
                    "agent_id": agent_id,
                    "task_type": "documentation",
                    "title": "Trace Task",
                    "description": "Task for decision trace endpoint",
                }
            ),
            content_type="application/json",
        )
        task_id = json.loads(task_response.data)["data"]["id"]

        trace_response = client.get(f"/api/tasks/{task_id}/decision-trace")
        trace_data = json.loads(trace_response.data)

        assert trace_response.status_code == 200
        assert trace_data["success"] is True
        assert trace_data["data"]["task"]["id"] == task_id
        assert "timeline" in trace_data["data"]

    def test_list_rules_and_init_defaults(self, client):
        init_response = client.post("/api/governance/init-defaults")
        init_data = json.loads(init_response.data)
        list_response = client.get("/api/governance/rules")
        list_data = json.loads(list_response.data)

        assert init_response.status_code == 200
        assert init_data["success"] is True
        assert list_response.status_code == 200
        assert list_data["count"] >= 5

    def test_dashboard_summary(self, client):
        response = client.get("/api/dashboard/summary")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert "agents" in data["data"]

    def test_dashboard_live_alerts(self, client):
        response = client.get("/api/dashboard/live-alerts?limit=5&days=2")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert "data" in data

    def test_audit_logs(self, client):
        response = client.get("/api/audit/logs")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True


class TestAgentService:
    def test_register_agent(self, session):
        service = AgentService(session)

        agent = service.register_agent(
            name="Service Test Agent",
            agent_type="monitoring",
            description="Test agent",
            capabilities=["log_analysis"],
        )

        assert agent is not None
        assert agent.name == "Service Test Agent"

    def test_get_agent_statistics(self, session, sample_agent, sample_task):
        service = AgentService(session)
        stats = service.get_agent_statistics(sample_agent.id)

        assert "total_tasks" in stats
        assert "task_type_distribution" in stats
        assert "drift" in stats
        assert "behavior_baseline" in stats


class TestTaskService:
    def test_create_task(self, session, sample_agent):
        service = TaskService(session)

        task, evaluation = service.create_task(
            agent_id=sample_agent.id,
            task_type="documentation",
            title="Service Test Task",
            description="Test task",
        )

        assert task.title == "Service Test Task"
        assert "risk_assessment" in evaluation
        assert "governance" in evaluation

    def test_reject_flagged_task(self, session, sample_agent):
        service = TaskService(session)
        task, _ = service.create_task(
            agent_id=sample_agent.id,
            task_type="documentation",
            title="Reject Me",
            description="Needs review",
        )
        task.flag_for_review("Manual review required")
        session.commit()

        rejected = service.reject_task(task.id, reviewer="manager-1", reason="Rejected for policy reasons")
        assert rejected.status == TaskStatus.REJECTED

    def test_get_task_decision_trace(self, session, sample_agent):
        service = TaskService(session)
        task, _ = service.create_task(
            agent_id=sample_agent.id,
            task_type="documentation",
            title="Trace Service Task",
            description="Task for decision trace service method",
        )

        trace = service.get_task_decision_trace(task.id)

        assert trace["task"]["id"] == task.id
        assert "decision" in trace
        assert "explainability" in trace
        assert "top_risk_factors" in trace["explainability"]
        assert isinstance(trace["timeline"], list)


class TestAuditService:
    def test_log_creation(self, session):
        service = AuditService(session)

        log = service.log_action(
            action=AuditAction.SYSTEM_ERROR,
            entity_type="system",
            entity_id="system-1",
            details={"message": "Test error"},
            severity="error",
        )

        assert log is not None
        assert log.entity_type == "system"
        assert log.severity == "error"

    def test_query_logs(self, session):
        service = AuditService(session)
        service.log_action(
            action=AuditAction.SYSTEM_ERROR,
            entity_type="system",
            entity_id="system-1",
            details={"message": "Test error"},
            severity="error",
        )

        logs = service.get_audit_logs(limit=10)

        assert isinstance(logs, list)
        assert len(logs) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
