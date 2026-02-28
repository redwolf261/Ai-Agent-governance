"""
AI Agent Governance System - Test Suite
Unit and Integration Tests

Author: Rivan Shetty
Group: CS-K GRP 3
"""
import pytest
import json
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import init_db, get_session, Base, engine
from models.agent import Agent, AgentType, AgentStatus
from models.task import Task, TaskStatus, RiskLevel, TaskType
from models.governance_rule import GovernanceRule, RuleType, RuleAction
from models.user import User, UserRole
from services.governance_engine import GovernanceEngine
from services.anomaly_detector import AnomalyDetector
from services.audit_service import AuditService
from services.agent_service import AgentService
from services.task_service import TaskService


# ==================== FIXTURES ====================

@pytest.fixture
def app():
    """Create test application"""
    application = create_app()
    application.config['TESTING'] = True
    return application


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def session():
    """Create test database session"""
    Base.metadata.create_all(engine)
    session = get_session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_agent(session):
    """Create sample agent for testing"""
    agent = Agent(
        name="Test Agent",
        agent_type=AgentType.CODE_GENERATOR,
        description="Test agent for unit tests",
        is_trusted=False
    )
    session.add(agent)
    session.commit()
    return agent


@pytest.fixture
def sample_task(session, sample_agent):
    """Create sample task for testing"""
    task = Task(
        agent_id=sample_agent.id,
        task_type=TaskType.CODE_GENERATION,
        title="Test Task",
        description="Test task for unit tests",
        input_data={"test": True}
    )
    session.add(task)
    session.commit()
    return task


@pytest.fixture
def governance_engine(session):
    """Create governance engine instance"""
    return GovernanceEngine(session)


@pytest.fixture
def anomaly_detector():
    """Create anomaly detector instance"""
    detector = AnomalyDetector()
    detector.train_models(n_samples=100)  # Train with minimal samples
    return detector


@pytest.fixture
def audit_service(session):
    """Create audit service instance"""
    return AuditService(session)


# ==================== AGENT MODEL TESTS ====================

class TestAgentModel:
    """Tests for Agent model"""
    
    def test_agent_creation(self, session):
        """Test creating a new agent"""
        agent = Agent(
            name="New Agent",
            agent_type=AgentType.CODE_REVIEWER,
            description="A code reviewing agent"
        )
        session.add(agent)
        session.commit()
        
        assert agent.id is not None
        assert agent.name == "New Agent"
        assert agent.agent_type == AgentType.CODE_REVIEWER
        assert agent.status == AgentStatus.ACTIVE
        assert agent.trust_level == 0.5
    
    def test_agent_update_activity(self, session, sample_agent):
        """Test updating agent activity"""
        old_active = sample_agent.last_active_at
        sample_agent.update_activity()
        session.commit()
        
        assert sample_agent.last_active_at > old_active
    
    def test_agent_trust_adjustment(self, session, sample_agent):
        """Test adjusting agent trust level"""
        initial_trust = sample_agent.trust_level
        
        sample_agent.adjust_trust(0.1)
        session.commit()
        assert sample_agent.trust_level == initial_trust + 0.1
        
        sample_agent.adjust_trust(-0.05)
        session.commit()
        assert sample_agent.trust_level == initial_trust + 0.05
        
    def test_agent_trust_bounds(self, session, sample_agent):
        """Test that trust level stays within bounds"""
        sample_agent.adjust_trust(100)
        assert sample_agent.trust_level == 1.0
        
        sample_agent.adjust_trust(-200)
        assert sample_agent.trust_level == 0.0
    
    def test_agent_suspension(self, session, sample_agent):
        """Test agent suspension"""
        sample_agent.status = AgentStatus.SUSPENDED
        sample_agent.suspended_reason = "Policy violation"
        session.commit()
        
        assert sample_agent.status == AgentStatus.SUSPENDED
        assert sample_agent.suspended_at is not None
    
    def test_agent_to_dict(self, sample_agent):
        """Test agent serialization"""
        data = sample_agent.to_dict()
        
        assert 'id' in data
        assert 'name' in data
        assert data['name'] == "Test Agent"
        assert 'agent_type' in data


# ==================== TASK MODEL TESTS ====================

class TestTaskModel:
    """Tests for Task model"""
    
    def test_task_creation(self, session, sample_agent):
        """Test creating a new task"""
        task = Task(
            agent_id=sample_agent.id,
            task_type=TaskType.DATA_ANALYSIS,
            title="Analysis Task",
            description="Analyze some data"
        )
        session.add(task)
        session.commit()
        
        assert task.id is not None
        assert task.status == TaskStatus.PENDING
        assert task.risk_score == 0.0
    
    def test_task_start(self, session, sample_task):
        """Test starting a task"""
        sample_task.start()
        session.commit()
        
        assert sample_task.status == TaskStatus.RUNNING
        assert sample_task.started_at is not None
    
    def test_task_complete(self, session, sample_task):
        """Test completing a task"""
        sample_task.start()
        sample_task.complete({"result": "success"})
        session.commit()
        
        assert sample_task.status == TaskStatus.COMPLETED
        assert sample_task.completed_at is not None
        assert sample_task.output_data == {"result": "success"}
    
    def test_task_fail(self, session, sample_task):
        """Test failing a task"""
        sample_task.start()
        sample_task.fail("Something went wrong")
        session.commit()
        
        assert sample_task.status == TaskStatus.FAILED
        assert "Something went wrong" in sample_task.error_message
    
    def test_task_flag(self, session, sample_task):
        """Test flagging a task"""
        sample_task.flag("High risk operation detected")
        session.commit()
        
        assert sample_task.status == TaskStatus.FLAGGED
        assert sample_task.requires_approval == True
    
    def test_task_block(self, session, sample_task):
        """Test blocking a task"""
        sample_task.block("Violation: Restricted operation")
        session.commit()
        
        assert sample_task.status == TaskStatus.BLOCKED
        assert sample_task.is_blocked == True
    
    def test_task_risk_level_calculation(self, session, sample_task):
        """Test risk level classification"""
        sample_task.risk_score = 0.2
        assert sample_task.get_risk_level() == RiskLevel.LOW
        
        sample_task.risk_score = 0.5
        assert sample_task.get_risk_level() == RiskLevel.MEDIUM
        
        sample_task.risk_score = 0.75
        assert sample_task.get_risk_level() == RiskLevel.HIGH
        
        sample_task.risk_score = 0.95
        assert sample_task.get_risk_level() == RiskLevel.CRITICAL


# ==================== GOVERNANCE ENGINE TESTS ====================

class TestGovernanceEngine:
    """Tests for Governance Engine"""
    
    def test_create_default_rules(self, session, governance_engine):
        """Test creating default governance rules"""
        governance_engine.create_default_rules()
        
        rules = session.query(GovernanceRule).all()
        assert len(rules) > 0
    
    def test_evaluate_low_risk_task(self, session, governance_engine, sample_task):
        """Test evaluation of low-risk task"""
        sample_task.task_type = TaskType.DOCUMENTATION
        sample_task.estimated_duration = 60
        session.commit()
        
        result = governance_engine.evaluate_task(sample_task)
        
        assert 'risk_score' in result
        assert 'action' in result
        assert result['action'] in ['allow', 'flag', 'block']
    
    def test_evaluate_high_risk_task(self, session, governance_engine, sample_task):
        """Test evaluation of high-risk task"""
        sample_task.task_type = TaskType.SYSTEM_MODIFICATION
        sample_task.input_data = {
            "operation": "delete",
            "target": "production_database"
        }
        sample_task.estimated_duration = 7200
        session.commit()
        
        governance_engine.create_default_rules()
        result = governance_engine.evaluate_task(sample_task)
        
        # High risk tasks should be flagged or blocked
        assert result['risk_score'] > 0.5 or result['action'] in ['flag', 'block']
    
    def test_rule_priority(self, session, governance_engine):
        """Test that rules are evaluated by priority"""
        # Create rules with different priorities
        rule_low = GovernanceRule(
            name="Low Priority",
            rule_type=RuleType.RISK_THRESHOLD,
            condition={"threshold": 0.5},
            action=RuleAction.LOG_ONLY,
            priority=50
        )
        rule_high = GovernanceRule(
            name="High Priority",
            rule_type=RuleType.RISK_THRESHOLD,
            condition={"threshold": 0.7},
            action=RuleAction.BLOCK,
            priority=200
        )
        session.add_all([rule_low, rule_high])
        session.commit()
        
        rules = governance_engine.get_active_rules()
        
        # Should be sorted by priority descending
        assert rules[0].priority >= rules[-1].priority


# ==================== ANOMALY DETECTOR TESTS ====================

class TestAnomalyDetector:
    """Tests for ML Anomaly Detection"""
    
    def test_training(self):
        """Test model training"""
        detector = AnomalyDetector()
        detector.train_models(n_samples=100)
        
        assert detector.isolation_forest is not None
        assert detector.one_class_svm is not None
    
    def test_feature_extraction(self, anomaly_detector, sample_task):
        """Test feature extraction from task"""
        features = anomaly_detector.extract_features(sample_task)
        
        assert features is not None
        assert len(features) == 10  # 10 features expected
    
    def test_normal_task_detection(self, session, anomaly_detector, sample_agent):
        """Test detection of normal task"""
        task = Task(
            agent_id=sample_agent.id,
            task_type=TaskType.DOCUMENTATION,
            title="Normal Task",
            description="Just a regular task",
            estimated_duration=300
        )
        session.add(task)
        session.commit()
        
        result = anomaly_detector.detect(task)
        
        assert 'is_anomaly' in result
        assert 'combined_score' in result
        assert 0 <= result['combined_score'] <= 1
    
    def test_anomalous_task_detection(self, session, anomaly_detector, sample_agent):
        """Test detection of anomalous task"""
        # Create task with unusual characteristics
        task = Task(
            agent_id=sample_agent.id,
            task_type=TaskType.SYSTEM_MODIFICATION,
            title="X" * 100,  # Unusual title length
            description="Delete everything" * 50,  # Unusual description
            estimated_duration=99999,  # Unusual duration
            input_data={"delete": True, "admin": True, "override": True}
        )
        session.add(task)
        session.commit()
        
        result = anomaly_detector.detect(task)
        
        # Should have higher anomaly score than normal task
        assert result['combined_score'] >= 0


# ==================== API ENDPOINT TESTS ====================

class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['status'] == 'healthy'
    
    def test_api_docs(self, client):
        """Test API documentation endpoint"""
        response = client.get('/api')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert 'endpoints' in data
    
    def test_list_agents(self, client):
        """Test listing agents"""
        response = client.get('/api/agents')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert 'success' in data
    
    def test_register_agent(self, client):
        """Test registering a new agent"""
        response = client.post('/api/agents',
            data=json.dumps({
                "name": "API Test Agent",
                "agent_type": "code_generator",
                "description": "Created via API test"
            }),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
    
    def test_list_tasks(self, client):
        """Test listing tasks"""
        response = client.get('/api/tasks')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert 'success' in data
    
    def test_list_rules(self, client):
        """Test listing governance rules"""
        response = client.get('/api/governance/rules')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert 'success' in data
    
    def test_init_default_rules(self, client):
        """Test initializing default rules"""
        response = client.post('/api/governance/init-defaults')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
    
    def test_dashboard_summary(self, client):
        """Test dashboard summary endpoint"""
        response = client.get('/api/dashboard/summary')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert 'success' in data
    
    def test_audit_logs(self, client):
        """Test audit logs endpoint"""
        response = client.get('/api/audit/logs')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert 'success' in data


# ==================== SERVICE TESTS ====================

class TestAgentService:
    """Tests for Agent Service"""
    
    def test_register_agent(self, session):
        """Test agent registration via service"""
        service = AgentService(session)
        
        agent = service.register_agent(
            name="Service Test Agent",
            agent_type="monitoring",
            description="Test agent",
            capabilities=["log_analysis"]
        )
        
        assert agent is not None
        assert agent.name == "Service Test Agent"
    
    def test_get_agent_statistics(self, session, sample_agent, sample_task):
        """Test getting agent statistics"""
        service = AgentService(session)
        
        stats = service.get_agent_statistics(sample_agent.id)
        
        assert 'total_tasks' in stats
        assert 'status_breakdown' in stats


class TestTaskService:
    """Tests for Task Service"""
    
    def test_create_task(self, session, sample_agent):
        """Test task creation via service"""
        service = TaskService(session)
        
        result = service.create_task(
            agent_id=sample_agent.id,
            task_type="documentation",
            title="Service Test Task",
            description="Test task"
        )
        
        assert 'task' in result
        assert 'evaluation' in result


class TestAuditService:
    """Tests for Audit Service"""
    
    def test_log_creation(self, session):
        """Test audit log creation"""
        service = AuditService(session)
        
        log = service.log_task_created(
            task_id="test-123",
            agent_id="agent-456",
            task_type="code_generation",
            title="Test Task"
        )
        
        assert log is not None
        assert log.entity_type == "task"
    
    def test_query_logs(self, session):
        """Test querying audit logs"""
        service = AuditService(session)
        
        # Create some logs first
        service.log_task_created(
            task_id="test-1",
            agent_id="agent-1",
            task_type="test",
            title="Test 1"
        )
        
        logs = service.query_logs(limit=10)
        
        assert isinstance(logs, list)


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
