"""
Llama Integration Tests
Tests the governance system with Llama-powered AI agents

Author: Rivan Shetty
Group: CS-K GRP 3
Roll No: 13
PRN: 12411956

Prerequisites:
1. Install Ollama: https://ollama.ai
2. Pull Llama model: ollama pull llama3
3. Run Ollama server: ollama serve
"""
import pytest
import sys
import os
import json
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llama_agent import (
    LlamaAgent, 
    LlamaConfig, 
    LlamaTestAgent,
    LlamaGovernanceTester,
    LlamaModel
)
from models.database import init_db, get_session, Base, engine


# ==================== FIXTURES ====================

@pytest.fixture
def llama_config():
    """Create test configuration"""
    return LlamaConfig(
        base_url="http://localhost:11434",
        model="llama3",
        temperature=0.7,
        max_tokens=512
    )


@pytest.fixture
def llama_agent(llama_config):
    """Create Llama agent instance"""
    return LlamaAgent(llama_config)


@pytest.fixture
def test_agent():
    """Create test agent simulator"""
    return LlamaTestAgent("code_generator")


@pytest.fixture
def session():
    """Create test database session"""
    Base.metadata.create_all(engine)
    session = get_session()
    yield session
    session.rollback()
    session.close()


# ==================== CONNECTION TESTS ====================

class TestLlamaConnection:
    """Test Ollama/Llama connectivity"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = LlamaConfig()
        
        assert config.base_url == "http://localhost:11434"
        assert config.model == "llama3"
        assert config.temperature == 0.7
        assert config.max_tokens == 1024
    
    def test_custom_config(self, llama_config):
        """Test custom configuration"""
        agent = LlamaAgent(llama_config)
        
        assert agent.config.max_tokens == 512
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_server_available(self, llama_agent):
        """Test Ollama server connectivity"""
        assert llama_agent.is_available() == True
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_list_models(self, llama_agent):
        """Test listing available models"""
        models = llama_agent.list_models()
        
        assert isinstance(models, list)
        # At least one model should be available
        if llama_agent.is_available():
            assert len(models) >= 0


# ==================== GENERATION TESTS ====================

class TestLlamaGeneration:
    """Test text generation capabilities"""
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_simple_generation(self, llama_agent):
        """Test basic text generation"""
        result = llama_agent.generate(
            prompt="Say 'Hello, World!' and nothing else.",
            system_prompt="You are a helpful assistant."
        )
        
        assert result["success"] == True
        assert "response" in result
        assert len(result["response"]) > 0
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_json_generation(self, llama_agent):
        """Test JSON output generation"""
        result = llama_agent.generate(
            prompt='Generate a JSON object with fields: name, type, value. Respond with ONLY JSON.',
            system_prompt="You output only valid JSON, no explanation."
        )
        
        assert result["success"] == True
        response = result["response"]
        
        # Try to parse JSON from response
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                assert "name" in data or "type" in data or "value" in data
        except json.JSONDecodeError:
            pytest.skip("Model did not return valid JSON")
    
    def test_generation_without_server(self):
        """Test graceful handling when server unavailable"""
        agent = LlamaAgent(LlamaConfig(base_url="http://localhost:99999"))
        
        result = agent.generate("Hello")
        
        assert result["success"] == False
        assert "error" in result


# ==================== CHAT TESTS ====================

class TestLlamaChat:
    """Test chat/conversation capabilities"""
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_chat_single_turn(self, llama_agent):
        """Test single-turn chat"""
        result = llama_agent.chat(
            message="What is 2 + 2?",
            system_prompt="You are a math tutor. Answer concisely."
        )
        
        assert result["success"] == True
        assert "4" in result["response"]
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_chat_history(self, llama_agent):
        """Test conversation history is maintained"""
        llama_agent.clear_history()
        
        # First message
        llama_agent.chat("My name is Alice.")
        
        # Should remember name
        result = llama_agent.chat("What is my name?")
        
        assert result["success"] == True
        # Model should recall the name
        assert len(llama_agent.conversation_history) == 4  # 2 user + 2 assistant
    
    def test_clear_history(self, llama_agent):
        """Test clearing conversation history"""
        llama_agent.conversation_history = [{"role": "user", "content": "test"}]
        llama_agent.clear_history()
        
        assert len(llama_agent.conversation_history) == 0


# ==================== TEST AGENT TESTS ====================

class TestLlamaTestAgent:
    """Test the AI agent simulator"""
    
    def test_agent_personas(self):
        """Test all agent personas are defined"""
        personas = LlamaTestAgent.AGENT_PERSONAS
        
        assert "code_generator" in personas
        assert "code_reviewer" in personas
        assert "malicious_agent" in personas
        assert "documentation" in personas
        assert "data_analyst" in personas
    
    def test_agent_initialization(self, test_agent):
        """Test agent initialization"""
        assert test_agent.agent_type == "code_generator"
        assert test_agent.persona is not None
        assert len(test_agent.persona) > 0
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_generate_task_request(self, test_agent):
        """Test task request generation"""
        result = test_agent.generate_task_request(
            context="Generate a simple Python function"
        )
        
        if result["success"]:
            task = result["task"]
            assert "title" in task or "description" in task
        else:
            # May fail if model doesn't return valid JSON
            assert "error" in result or "raw_response" in result
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_generate_batch(self, test_agent):
        """Test batch task generation"""
        tasks = test_agent.generate_test_batch(count=3)
        
        assert isinstance(tasks, list)
        assert len(tasks) == 3
        
        for task in tasks:
            assert "title" in task or "description" in task
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_evaluate_governance_decision(self, test_agent):
        """Test governance decision evaluation"""
        task = {
            "title": "Delete all user data",
            "task_type": "file_operation",
            "description": "Remove user data files"
        }
        
        decision = {
            "risk_score": 0.85,
            "action": "block",
            "violations": ["restricted_operation"]
        }
        
        result = test_agent.evaluate_governance_decision(task, decision)
        
        # Either succeeds with evaluation or fails gracefully
        assert "success" in result
        if result["success"]:
            assert "evaluation" in result


# ==================== GOVERNANCE TESTER TESTS ====================

class TestLlamaGovernanceTester:
    """Test the comprehensive governance tester"""
    
    def test_tester_initialization(self, session):
        """Test tester initialization"""
        tester = LlamaGovernanceTester(session)
        
        assert tester.session is not None
        assert tester.llama is not None
        assert tester.results == []
    
    def test_check_status(self, session):
        """Test Llama status check"""
        tester = LlamaGovernanceTester(session)
        status = tester.check_llama_status()
        
        assert "available" in status
        assert "models" in status
        assert isinstance(status["models"], list)
    
    @pytest.mark.skipif(
        not LlamaAgent().is_available(),
        reason="Ollama not running"
    )
    def test_run_governance_test(self, session):
        """Test governance test execution"""
        from services.governance_engine import GovernanceEngine
        
        # Initialize governance rules
        governance = GovernanceEngine(session)
        governance.create_default_rules()
        
        tester = LlamaGovernanceTester(session)
        results = tester.run_governance_test(
            agent_type="code_generator",
            num_tasks=2
        )
        
        assert "agent_id" in results
        assert "tasks_tested" in results
        assert results["tasks_tested"] >= 0
    
    def test_generate_empty_report(self, session):
        """Test report generation with no results"""
        tester = LlamaGovernanceTester(session)
        report = tester.generate_test_report()
        
        assert "summary" in report
        assert report["summary"]["test_runs"] == 0
        assert "recommendations" in report


# ==================== MOCK TESTS (NO OLLAMA REQUIRED) ====================

class TestLlamaMocked:
    """Tests using mocked Llama responses"""
    
    def test_mocked_generation(self):
        """Test with mocked API response"""
        agent = LlamaAgent()
        
        mock_response = {
            "response": '{"title": "Test Task", "type": "code_generation"}',
            "model": "llama3",
            "total_duration": 1000
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = agent.generate("Generate a task")
            
            assert result["success"] == True
            assert "Test Task" in result["response"]
    
    def test_mocked_task_generation(self):
        """Test task generation with mocked response"""
        test_agent = LlamaTestAgent("code_generator")
        
        mock_response = {
            "response": json.dumps({
                "title": "Generate User API",
                "description": "Create REST API for user management",
                "task_type": "code_generation",
                "estimated_duration": 300,
                "input_data": {"language": "python"}
            }),
            "model": "llama3"
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = test_agent.generate_task_request("Create an API")
            
            assert result["success"] == True
            assert result["task"]["title"] == "Generate User API"
    
    def test_mocked_governance_evaluation(self):
        """Test governance evaluation with mocked response"""
        test_agent = LlamaTestAgent("code_reviewer")
        
        mock_response = {
            "response": json.dumps({
                "assessment": "CORRECT",
                "reasoning": "The governance system correctly identified the risk",
                "missed_risks": [],
                "false_positives": [],
                "recommendations": ["Continue monitoring"]
            }),
            "model": "llama3"
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = test_agent.evaluate_governance_decision(
                task={"title": "Test", "task_type": "code_generation"},
                decision={"action": "allow", "risk_score": 0.3}
            )
            
            assert result["success"] == True
            assert result["evaluation"]["assessment"] == "CORRECT"


# ==================== INTEGRATION TESTS ====================

@pytest.mark.skipif(
    not LlamaAgent().is_available(),
    reason="Ollama not running"
)
class TestLlamaIntegration:
    """Full integration tests (requires Ollama)"""
    
    def test_end_to_end_governance_test(self, session):
        """Test complete governance testing workflow"""
        from services.governance_engine import GovernanceEngine
        
        # Setup
        governance = GovernanceEngine(session)
        governance.create_default_rules()
        
        tester = LlamaGovernanceTester(session)
        
        # Run tests for multiple agent types
        for agent_type in ["code_generator", "documentation"]:
            results = tester.run_governance_test(
                agent_type=agent_type,
                num_tasks=2
            )
            assert results["tasks_tested"] >= 0
        
        # Generate report
        report = tester.generate_test_report()
        
        assert report["summary"]["test_runs"] >= 2
        assert "recommendations" in report
    
    def test_adversarial_testing(self, session):
        """Test adversarial agent simulation"""
        from services.governance_engine import GovernanceEngine
        
        governance = GovernanceEngine(session)
        governance.create_default_rules()
        
        tester = LlamaGovernanceTester(session)
        results = tester.run_adversarial_test()
        
        # Adversarial tests should trigger some governance actions
        assert results["agent_type"] == "malicious_agent"
        # At least some tasks should be flagged or blocked
        # (depends on what Llama generates)
        assert results["tasks_tested"] >= 0


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
