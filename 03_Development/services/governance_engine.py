"""
Governance Engine
Core rule evaluation and policy enforcement system
"""
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.task import Task, TaskStatus, RiskLevel
from models.agent import Agent, AgentStatus
from models.governance_rule import GovernanceRule, RuleType, RuleAction
from models.audit_log import AuditLog, AuditAction, create_audit_log
from utils.time_utils import utc_now


class GovernanceEngine:
    """
    Core governance engine for evaluating AI agent tasks against defined rules.
    
    The engine processes tasks through a rule pipeline, evaluating each
    active rule in priority order and determining the appropriate action.
    """
    
    def __init__(self, db: Session):
        """
        Initialize governance engine with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._rule_cache: Dict[str, GovernanceRule] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes cache TTL
    
    def evaluate_task(self, task: Task, agent: Agent) -> Tuple[str, List[Dict]]:
        """
        Evaluate a task against all applicable governance rules.
        
        Args:
            task: The task to evaluate
            agent: The agent executing the task
        
        Returns:
            Tuple of (final_status, list of triggered rules with details)
        """
        triggered_rules = []
        final_status = "approved"
        
        # Get applicable rules
        rules = self._get_applicable_rules(task, agent)
        
        for rule in rules:
            result = self._evaluate_rule(rule, task, agent)
            
            if result["triggered"]:
                triggered_rules.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "rule_type": rule.rule_type.value,
                    "action": rule.action.value,
                    "severity": rule.severity.value,
                    "reason": result["reason"]
                })
                
                # Log rule trigger
                self._log_rule_trigger(rule, task, agent, result["reason"])
                
                # Determine final status based on action
                if rule.action == RuleAction.BLOCK:
                    final_status = "blocked"
                    break  # Stop processing on block
                elif rule.action == RuleAction.FLAG and final_status != "blocked":
                    final_status = "flagged"
                elif rule.action == RuleAction.REQUIRE_APPROVAL and final_status not in ["blocked", "flagged"]:
                    final_status = "pending_approval"
                elif rule.action == RuleAction.ESCALATE and final_status not in ["blocked", "flagged"]:
                    final_status = "escalated"
        
        return final_status, triggered_rules
    
    def _get_applicable_rules(self, task: Task, agent: Agent) -> List[GovernanceRule]:
        """
        Get all active rules applicable to the task and agent.
        
        Returns rules sorted by priority (lower number = higher priority).
        """
        # Refresh cache if needed
        self._refresh_cache_if_needed()
        
        applicable_rules = []
        
        for rule in self._rule_cache.values():
            if not rule.is_currently_effective():
                continue
            
            if not rule.is_applicable_to_agent(agent.id):
                continue
            
            if not rule.is_applicable_to_task_type(task.task_type.value):
                continue
            
            applicable_rules.append(rule)
        
        # Sort by priority
        applicable_rules.sort(key=lambda r: r.priority)
        
        return applicable_rules
    
    def _evaluate_rule(self, rule: GovernanceRule, task: Task, agent: Agent) -> Dict[str, Any]:
        """
        Evaluate a single rule against the task.
        
        Returns:
            Dict with 'triggered' (bool) and 'reason' (str) keys
        """
        try:
            condition = json.loads(rule.condition)
        except json.JSONDecodeError:
            return {"triggered": False, "reason": "Invalid rule condition"}
        
        # Evaluate based on rule type
        evaluators = {
            RuleType.TASK_TYPE_RESTRICTION: self._evaluate_task_type_restriction,
            RuleType.EXECUTION_TIME_LIMIT: self._evaluate_execution_time_limit,
            RuleType.RESOURCE_ACCESS: self._evaluate_resource_access,
            RuleType.DATA_SENSITIVITY: self._evaluate_data_sensitivity,
            RuleType.OPERATION_RESTRICTION: self._evaluate_operation_restriction,
            RuleType.RISK_THRESHOLD: self._evaluate_risk_threshold,
            RuleType.AGENT_TRUST_LEVEL: self._evaluate_agent_trust_level,
            RuleType.RATE_LIMIT: self._evaluate_rate_limit,
            RuleType.PAYLOAD_SCAN: self._evaluate_payload_scan,
        }
        
        evaluator = evaluators.get(rule.rule_type)
        if evaluator:
            return evaluator(condition, task, agent)
        
        return {"triggered": False, "reason": "Unknown rule type"}
    
    def _evaluate_task_type_restriction(
        self, condition: Dict, task: Task, agent: Agent
    ) -> Dict[str, Any]:
        """Check if task type is restricted"""
        restricted_types = condition.get("restricted_types", [])
        
        if task.task_type.value in restricted_types:
            return {
                "triggered": True,
                "reason": f"Task type '{task.task_type.value}' is restricted"
            }
        
        return {"triggered": False, "reason": ""}
    
    def _evaluate_execution_time_limit(
        self, condition: Dict, task: Task, agent: Agent
    ) -> Dict[str, Any]:
        """Check if estimated execution time exceeds limit"""
        max_seconds = condition.get("max_seconds", 300)
        
        # Parse input data for estimated time
        try:
            input_data = json.loads(task.input_data or "{}")
            estimated_time = input_data.get("estimated_execution_time", 0)
            
            if estimated_time > max_seconds:
                return {
                    "triggered": True,
                    "reason": f"Estimated execution time ({estimated_time}s) exceeds limit ({max_seconds}s)"
                }
        except:
            pass
        
        return {"triggered": False, "reason": ""}
    
    def _evaluate_resource_access(
        self, condition: Dict, task: Task, agent: Agent
    ) -> Dict[str, Any]:
        """Check for restricted resource access"""
        restricted_resources = condition.get("restricted_resources", [])
        
        try:
            input_data = json.loads(task.input_data or "{}")
            requested_resources = input_data.get("resources", [])
            
            for resource in requested_resources:
                if any(rr in resource for rr in restricted_resources):
                    return {
                        "triggered": True,
                        "reason": f"Access to restricted resource: {resource}"
                    }
        except:
            pass
        
        return {"triggered": False, "reason": ""}
    
    def _evaluate_data_sensitivity(
        self, condition: Dict, task: Task, agent: Agent
    ) -> Dict[str, Any]:
        """Check for sensitive data patterns in task"""
        patterns = condition.get("sensitive_patterns", [])
        
        # Check task description and input data
        content_to_check = f"{task.description or ''} {task.input_data or ''}"
        
        for pattern in patterns:
            if re.search(pattern, content_to_check, re.IGNORECASE):
                return {
                    "triggered": True,
                    "reason": f"Sensitive data pattern detected"
                }
        
        return {"triggered": False, "reason": ""}
    
    def _evaluate_operation_restriction(
        self, condition: Dict, task: Task, agent: Agent
    ) -> Dict[str, Any]:
        """Check for restricted operations"""
        restricted_ops = condition.get("restricted_operations", [])
        
        try:
            input_data = json.loads(task.input_data or "{}")
            operation = input_data.get("operation", "")
            
            if operation in restricted_ops:
                return {
                    "triggered": True,
                    "reason": f"Operation '{operation}' is restricted"
                }
        except:
            pass
        
        return {"triggered": False, "reason": ""}
    
    def _evaluate_risk_threshold(
        self, condition: Dict, task: Task, agent: Agent
    ) -> Dict[str, Any]:
        """Check if risk score exceeds threshold"""
        threshold = condition.get("threshold", 0.7)
        
        if task.risk_score >= threshold:
            return {
                "triggered": True,
                "reason": f"Risk score ({task.risk_score:.2f}) exceeds threshold ({threshold})"
            }
        
        return {"triggered": False, "reason": ""}
    
    def _evaluate_agent_trust_level(
        self, condition: Dict, task: Task, agent: Agent
    ) -> Dict[str, Any]:
        """Check agent trust level requirements"""
        require_trusted = condition.get("require_trusted", False)
        
        if require_trusted and not agent.is_trusted:
            return {
                "triggered": True,
                "reason": f"Agent '{agent.name}' is not in trusted list"
            }
        
        return {"triggered": False, "reason": ""}
    
    def _evaluate_rate_limit(
        self, condition: Dict, task: Task, agent: Agent
    ) -> Dict[str, Any]:
        """Check if agent has exceeded rate limit"""
        max_tasks_per_hour = condition.get("max_tasks_per_hour", 100)
        
        # Count tasks in last hour
        from datetime import timedelta
        one_hour_ago = utc_now() - timedelta(hours=1)
        
        recent_task_count = self.db.query(Task).filter(
            Task.agent_id == agent.id,
            Task.created_at >= one_hour_ago
        ).count()
        
        if recent_task_count >= max_tasks_per_hour:
            return {
                "triggered": True,
                "reason": f"Agent rate limit exceeded ({recent_task_count}/{max_tasks_per_hour} tasks/hour)"
            }
        
        return {"triggered": False, "reason": ""}
    
    def _evaluate_payload_scan(
        self, condition: Dict, task: Task, agent: Agent
    ) -> Dict[str, Any]:
        """
        Recursively scan every field in the task payload for dangerous terms.

        Unlike _evaluate_operation_restriction (which does exact match on a single
        field), this method flattens the entire input_data JSON tree into one
        string and checks it against a regex blocklist — catching differently
        structured malicious payloads regardless of which field they appear in.
        """
        blocklist = condition.get("blocklist", [])
        if not blocklist:
            return {"triggered": False, "reason": ""}

        try:
            input_data = json.loads(task.input_data or "{}")
        except json.JSONDecodeError:
            return {"triggered": False, "reason": ""}

        # Collect every string token from the entire nested payload
        tokens = self._flatten_payload_strings(input_data)
        # Include task title and description so name-based evasion is caught too
        tokens.append(task.title or "")
        tokens.append(task.description or "")

        haystack = " ".join(tokens).lower()

        for term in blocklist:
            if re.search(term.lower(), haystack):
                return {
                    "triggered": True,
                    "reason": f"Dangerous payload content detected: '{term}'"
                }

        return {"triggered": False, "reason": ""}

    def _flatten_payload_strings(self, obj, depth: int = 0) -> List[str]:
        """Recursively extract every string token from a nested JSON structure."""
        if depth > 10:  # guard against adversarially deep nesting
            return []
        tokens = []
        if isinstance(obj, str):
            tokens.append(obj)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                tokens.append(str(k))
                tokens.extend(self._flatten_payload_strings(v, depth + 1))
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                tokens.extend(self._flatten_payload_strings(item, depth + 1))
        elif obj is not None:
            tokens.append(str(obj))
        return tokens

    def _refresh_cache_if_needed(self):
        """Refresh rule cache if expired or empty"""
        now = utc_now()
        
        if (self._cache_timestamp is None or 
            (now - self._cache_timestamp).total_seconds() > self._cache_ttl_seconds):
            
            rules = self.db.query(GovernanceRule).filter(
                GovernanceRule.is_active == True
            ).all()
            
            self._rule_cache = {rule.id: rule for rule in rules}
            self._cache_timestamp = now
    
    def _log_rule_trigger(
        self, rule: GovernanceRule, task: Task, agent: Agent, reason: str
    ):
        """Log when a rule is triggered"""
        audit_log = create_audit_log(
            action=AuditAction.RULE_TRIGGERED,
            entity_type="governance_rule",
            entity_id=rule.id,
            task_id=task.id,
            agent_id=agent.id,
            details=json.dumps({
                "rule_name": rule.name,
                "rule_type": rule.rule_type.value,
                "action": rule.action.value,
                "reason": reason
            }),
            severity="warning" if rule.action in [RuleAction.BLOCK, RuleAction.FLAG] else "info"
        )
        self.db.add(audit_log)
    
    def apply_governance_decision(
        self, task: Task, status: str, triggered_rules: List[Dict]
    ):
        """
        Apply governance decision to a task.
        
        Args:
            task: The task to update
            status: The governance status (approved, blocked, flagged, etc.)
            triggered_rules: List of triggered rule details
        """
        task.governance_status = status
        
        if status == "blocked":
            task.status = TaskStatus.BLOCKED
            task.governance_notes = f"Blocked by {len(triggered_rules)} rule(s)"
        elif status == "flagged":
            task.status = TaskStatus.FLAGGED
            task.governance_notes = f"Flagged by {len(triggered_rules)} rule(s) - requires review"
        elif status == "approved":
            task.governance_notes = "Approved - all rules passed"
        
        # Store triggered rules in governance notes
        if triggered_rules:
            task.governance_notes += f"\n\nTriggered Rules:\n"
            for rule in triggered_rules:
                task.governance_notes += f"- {rule['rule_name']}: {rule['reason']}\n"
        
        self.db.commit()
    
    def create_default_rules(self):
        """Create default governance rules for new installations"""
        default_rules = [
            {
                "name": "Deep Payload Threat Scan",
                "description": (
                    "Recursively scan every field in the task payload for dangerous terms. "
                    "Catches malicious operations regardless of which JSON key they appear in, "
                    "closing the gap left by single-field operation restriction checks."
                ),
                "rule_type": RuleType.PAYLOAD_SCAN,
                "condition": json.dumps({
                    "blocklist": [
                        # Destructive DB operations
                        "drop database", "drop table", "drop schema",
                        # Backdoors / C2
                        "backdoor", "reverse.?shell",
                        # Cryptojacking
                        "cryptominer", "cryptomining", "mining.pool",
                        # Ransomware
                        "ransomware", "ransom.note", "delete.backups",
                        # DDoS
                        "botnet", "http.flood", "ddos",
                        # Defense evasion
                        "stop.and.delete", "disable.alert", "disable.monitor",
                        # Exploitation
                        "privilege.*escalat", "cve-\\d{4}-\\d+",
                        # Exfiltration markers
                        "stolen.data", "attacker.server", "exfiltrat",
                        # Malicious infrastructure
                        "malicious.image", "compromised.node",
                        # Audit/trail suppression & unauthorized financial ops
                        "audit_trail.*disabled", "audit.*disabled",
                        "disable.*audit", "tamper.*log", "delete.*audit"
                    ]
                }),
                "action": RuleAction.BLOCK,
                "severity": "critical",
                "priority": 5  # Run before all other rules
            },
            {
                "name": "Block Dangerous Operations",
                "description": "Prevent execution of high-risk system operations",
                "rule_type": RuleType.OPERATION_RESTRICTION,
                "condition": json.dumps({
                    "restricted_operations": [
                        "database_delete",
                        "system_shutdown",
                        "credential_access",
                        "file_system_root_access"
                    ]
                }),
                "action": RuleAction.BLOCK,
                "severity": "critical",
                "priority": 10
            },
            {
                "name": "Flag High Risk Tasks",
                "description": "Flag tasks with risk score above 0.7 for review",
                "rule_type": RuleType.RISK_THRESHOLD,
                "condition": json.dumps({"threshold": 0.7}),
                "action": RuleAction.FLAG,
                "severity": "high",
                "priority": 20
            },
            {
                "name": "Execution Time Limit",
                "description": "Flag tasks exceeding 5 minute execution time",
                "rule_type": RuleType.EXECUTION_TIME_LIMIT,
                "condition": json.dumps({"max_seconds": 300}),
                "action": RuleAction.FLAG,
                "severity": "medium",
                "priority": 50
            },
            {
                "name": "Sensitive Data Protection",
                "description": "Detect and flag tasks involving sensitive data patterns",
                "rule_type": RuleType.DATA_SENSITIVITY,
                "condition": json.dumps({
                    "sensitive_patterns": [
                        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                        r"\b\d{16}\b",  # Credit card
                        r"password|secret|api_key|token|credential"
                    ]
                }),
                "action": RuleAction.FLAG,
                "severity": "high",
                "priority": 15
            },
            {
                "name": "Agent Rate Limiting",
                "description": "Limit agents to 100 tasks per hour",
                "rule_type": RuleType.RATE_LIMIT,
                "condition": json.dumps({"max_tasks_per_hour": 100}),
                "action": RuleAction.BLOCK,
                "severity": "medium",
                "priority": 30
            }
        ]
        
        for rule_data in default_rules:
            existing = self.db.query(GovernanceRule).filter(
                GovernanceRule.name == rule_data["name"]
            ).first()
            
            if not existing:
                rule = GovernanceRule(
                    name=rule_data["name"],
                    description=rule_data["description"],
                    rule_type=rule_data["rule_type"],
                    condition=rule_data["condition"],
                    action=rule_data["action"],
                    priority=rule_data["priority"],
                    created_by="system"
                )
                self.db.add(rule)
        
        self.db.commit()
        print("✅ Default governance rules created")
        
        # Return all active rules
        return self.db.query(GovernanceRule).filter(
            GovernanceRule.is_active == True
        ).all()
