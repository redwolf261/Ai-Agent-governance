"""
Advanced Governance Rules - Addressing Real-World Agent Concerns

This module implements governance rules that address the primary risks engineers
complain about: agents performing technically allowed but logically unintended actions.

Key Insight: "The primary risk of agentic AI is not incorrect reasoning, 
but correct reasoning applied to unsafe or unintended actions."

Author: Rivan Shetty
Group: CS-K GRP 3
Roll No: 13
PRN: 12411956
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models.governance_rule import GovernanceRule, RuleType, RuleAction, RuleSeverity
from services.governance_engine import GovernanceEngine


class BoundaryViolationDetector:
    """
    Detects when agents exceed their intended scope of action.
    
    Problem: Agents given broad permissions use them beyond task intent.
    Example: File system access → agent deletes unrelated files
    """
    
    @staticmethod
    def create_scope_restriction_rules(session: Session, governance: GovernanceEngine) -> List[GovernanceRule]:
        """Create rules preventing over-permissioned agent behavior"""
        rules = []
        
        # Rule 1: Production environment protection
        rules.append(governance.create_rule(
            name="Production Environment Boundary",
            rule_type=RuleType.CUSTOM,
            conditions={
                "input_data_contains": ["production", "prod", "live"],
                "excluded_operations": ["read", "view", "monitor"],
                "agent_trust_required": True
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Block modifications to production environments unless from trusted agents. "
                       "Addresses: Agents triggering cloud resources causing cost spikes."
        ))
        
        # Rule 2: File system scope boundaries
        rules.append(governance.create_rule(
            name="File System Scope Violation",
            rule_type=RuleType.CUSTOM,
            conditions={
                "operations": ["delete", "modify", "overwrite"],
                "path_indicators": ["..", "/root", "C:\\Windows", "system32"],
                "max_file_count": 10
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Prevent agents from modifying files outside assigned task scope. "
                       "Addresses: Agent deleting/modifying unrelated files."
        ))
        
        # Rule 3: Communication boundary violations
        rules.append(governance.create_rule(
            name="Unapproved Communication Actions",
            rule_type=RuleType.CUSTOM,
            conditions={
                "operations": ["send_email", "post_message", "create_ticket", "approve", "close"],
                "requires_approval": True
            },
            action=RuleAction.FLAG,
            severity=RuleSeverity.HIGH,
            description="Flag agents attempting to send emails, close tickets, or approve actions. "
                       "Addresses: Agents closing Jira tickets or sending notifications without approval."
        ))
        
        return rules


class GoalMisalignmentDetector:
    """
    Detects when agents technically achieve goals but violate intent.
    
    Problem: "Agent solved the KPI, not the problem"
    Example: "Resolve customer issue quickly" → agent refunds without authorization
    """
    
    @staticmethod
    def create_intent_alignment_rules(session: Session, governance: GovernanceEngine) -> List[GovernanceRule]:
        """Create rules preventing goal over-optimization"""
        rules = []
        
        # Rule 1: Financial action restrictions
        rules.append(governance.create_rule(
            name="Unauthorized Financial Actions",
            rule_type=RuleType.CUSTOM,
            conditions={
                "operations": ["refund", "credit", "payment", "transfer", "charge"],
                "threshold_amount": 100,
                "requires_human_approval": True
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Block agents from making financial decisions without authorization. "
                       "Addresses: Agents refunding money to 'resolve issues quickly'."
        ))
        
        # Rule 2: Verification bypass detection
        rules.append(governance.create_rule(
            name="Security Verification Bypass",
            rule_type=RuleType.CUSTOM,
            conditions={
                "bypassed_steps": ["verification", "authentication", "validation", "approval"],
                "shortcut_indicators": ["skip", "bypass", "ignore_check"]
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Prevent agents from bypassing verification steps to achieve goals faster. "
                       "Addresses: Agents skipping security checks to optimize task completion."
        ))
        
        # Rule 3: Alert silencing prevention
        rules.append(governance.create_rule(
            name="Alert Suppression Detection",
            rule_type=RuleType.CUSTOM,
            conditions={
                "operations": ["disable_alert", "silence_alarm", "mark_resolved", "ignore_error"],
                "without_root_cause_fix": True
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.HIGH,
            description="Block agents from silencing alerts instead of fixing root causes. "
                       "Addresses: Agents optimizing metrics by hiding problems."
        ))
        
        return rules


class ToolChainingGuardian:
    """
    Prevents unsafe combinations of tool usage.
    
    Problem: Agents chain benign tools into dangerous workflows
    Example: Tool A → Tool B → Tool C creates privilege escalation
    """
    
    @staticmethod
    def create_tool_chaining_rules(session: Session, governance: GovernanceEngine) -> List[GovernanceRule]:
        """Create rules preventing unsafe tool combinations"""
        rules = []
        
        # Rule 1: Privilege escalation chain detection
        rules.append(governance.create_rule(
            name="Indirect Privilege Escalation",
            rule_type=RuleType.CUSTOM,
            conditions={
                "tool_sequence": ["read_credentials", "authenticate", "execute_privileged"],
                "max_chain_depth": 3,
                "privilege_increase": True
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Detect and block tool chains that indirectly escalate privileges. "
                       "Addresses: Agents combining benign tools into dangerous workflows."
        ))
        
        # Rule 2: Data exfiltration chain
        rules.append(governance.create_rule(
            name="Multi-Step Data Exfiltration",
            rule_type=RuleType.CUSTOM,
            conditions={
                "pattern": ["read_data", "encode", "external_api_call"],
                "data_sensitivity": ["pii", "credentials", "financial"]
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Block multi-step data exfiltration patterns. "
                       "Addresses: Agents chaining tools to extract sensitive data."
        ))
        
        # Rule 3: Checkpoint requirements for chains
        rules.append(governance.create_rule(
            name="Tool Chain Human Checkpoint",
            rule_type=RuleType.CUSTOM,
            conditions={
                "chain_length": 4,
                "high_impact_operations": True,
                "requires_checkpoint": True
            },
            action=RuleAction.FLAG,
            severity=RuleSeverity.HIGH,
            description="Require human checkpoints for long tool chains with high impact. "
                       "Addresses: No human checkpoint between tool executions."
        ))
        
        return rules


class ImplicitNormEnforcer:
    """
    Encodes implicit human norms that agents don't naturally understand.
    
    Problem: Agents treat "allowed" as "encouraged"
    Example: Agents deploy code without review because they technically can
    """
    
    @staticmethod
    def create_implicit_norm_rules(session: Session, governance: GovernanceEngine) -> List[GovernanceRule]:
        """Create rules encoding implicit human norms"""
        rules = []
        
        # Rule 1: Production deployment requires review
        rules.append(governance.create_rule(
            name="Deployment Requires Review",
            rule_type=RuleType.CUSTOM,
            conditions={
                "operation": "deploy",
                "environment": ["production", "staging"],
                "requires_code_review": True,
                "requires_approval": True
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Enforce implicit norm: Never deploy without review. "
                       "Addresses: Agents deploying code automatically because they can."
        ))
        
        # Rule 2: Existing work preservation
        rules.append(governance.create_rule(
            name="Preserve Existing Work",
            rule_type=RuleType.CUSTOM,
            conditions={
                "operations": ["overwrite", "replace", "delete"],
                "target_has_content": True,
                "no_backup": True
            },
            action=RuleAction.FLAG,
            severity=RuleSeverity.HIGH,
            description="Protect existing work from being overwritten without backup. "
                       "Addresses: Agents overwriting configs because 'allowed' = 'encouraged'."
        ))
        
        # Rule 3: Read-before-write enforcement
        rules.append(governance.create_rule(
            name="Context Awareness Requirement",
            rule_type=RuleType.CUSTOM,
            conditions={
                "operation": "modify",
                "context_read": False,
                "impact": "high"
            },
            action=RuleAction.FLAG,
            severity=RuleSeverity.MEDIUM,
            description="Require agents to read context before making changes. "
                       "Addresses: Agents acting without understanding current state."
        ))
        
        return rules


class RunawayBehaviorPrevention:
    """
    Prevents agents from looping, repeating, or continuing beyond success.
    
    Problem: Absence of termination logic and guardrails
    Example: Agent loops tasks endlessly trying to optimize
    """
    
    @staticmethod
    def create_termination_rules(session: Session, governance: GovernanceEngine) -> List[GovernanceRule]:
        """Create rules preventing runaway agent behavior"""
        rules = []
        
        # Rule 1: Repetitive action detection
        rules.append(governance.create_rule(
            name="Repetitive Action Loop Detection",
            rule_type=RuleType.RATE_LIMIT,
            conditions={
                "same_operation_count": 5,
                "time_window_seconds": 60,
                "agent_id": "same"
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.HIGH,
            description="Block agents repeating same action multiple times. "
                       "Addresses: Agents looping tasks endlessly."
        ))
        
        # Rule 2: Success confirmation requirement
        rules.append(governance.create_rule(
            name="Continue After Success Prevention",
            rule_type=RuleType.CUSTOM,
            conditions={
                "previous_task_status": "completed",
                "attempting_retry": True,
                "error_present": False
            },
            action=RuleAction.FLAG,
            severity=RuleSeverity.MEDIUM,
            description="Flag agents continuing execution after achieving success. "
                       "Addresses: Agents not knowing when to stop."
        ))
        
        # Rule 3: Maximum task duration
        rules.append(governance.create_rule(
            name="Task Duration Ceiling",
            rule_type=RuleType.EXECUTION_TIME_LIMIT,
            conditions={
                "max_duration_seconds": 3600,
                "no_progress_timeout": 300
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.MEDIUM,
            description="Enforce maximum task duration to prevent runaway behavior. "
                       "Addresses: Agents executing indefinitely."
        ))
        
        return rules


class SecurityBoundaryEnforcer:
    """
    Prevents agents from collapsing "who can" vs "who should" distinctions.
    
    Problem: Agents bypass standard RBAC flows
    Example: Agent acts on behalf of users without strong identity binding
    """
    
    @staticmethod
    def create_security_boundary_rules(session: Session, governance: GovernanceEngine) -> List[GovernanceRule]:
        """Create rules enforcing security boundaries"""
        rules = []
        
        # Rule 1: Identity binding requirement
        rules.append(governance.create_rule(
            name="Strong Identity Binding",
            rule_type=RuleType.CUSTOM,
            conditions={
                "acting_on_behalf": True,
                "user_delegation": "required",
                "audit_trail": "required"
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Require explicit user delegation for privileged actions. "
                       "Addresses: Agents acting on behalf of users without authorization."
        ))
        
        # Rule 2: Data access scope validation
        rules.append(governance.create_rule(
            name="Data Access Boundary Enforcement",
            rule_type=RuleType.DATA_SENSITIVITY,
            conditions={
                "data_classification": ["confidential", "restricted", "pii"],
                "agent_clearance_required": True,
                "access_justification": "required"
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Prevent agents from accessing data outside their scope. "
                       "Addresses: Agents accessing data they weren't supposed to."
        ))
        
        # Rule 3: RBAC bypass detection
        rules.append(governance.create_rule(
            name="RBAC Flow Bypass Prevention",
            rule_type=RuleType.CUSTOM,
            conditions={
                "standard_workflow": "bypassed",
                "approval_chain": "skipped",
                "direct_privilege_use": True
            },
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL,
            description="Block attempts to bypass standard role-based access control flows. "
                       "Addresses: Agents collapsing 'who can' vs 'who should' distinction."
        ))
        
        return rules


def initialize_advanced_governance_rules(session: Session) -> Dict[str, List[GovernanceRule]]:
    """
    Initialize comprehensive governance rules addressing real-world agent concerns.
    
    Returns:
        Dictionary mapping concern categories to their rules
    """
    governance = GovernanceEngine(session)
    
    rules_by_category = {
        "boundary_violations": BoundaryViolationDetector.create_scope_restriction_rules(session, governance),
        "goal_misalignment": GoalMisalignmentDetector.create_intent_alignment_rules(session, governance),
        "unsafe_tool_chaining": ToolChainingGuardian.create_tool_chaining_rules(session, governance),
        "implicit_norm_violations": ImplicitNormEnforcer.create_implicit_norm_rules(session, governance),
        "runaway_behavior": RunawayBehaviorPrevention.create_termination_rules(session, governance),
        "security_boundaries": SecurityBoundaryEnforcer.create_security_boundary_rules(session, governance)
    }
    
    # Commit all rules
    for rules_list in rules_by_category.values():
        for rule in rules_list:
            session.add(rule)
    
    session.commit()
    
    total_rules = sum(len(rules) for rules in rules_by_category.values())
    print(f"✅ Initialized {total_rules} advanced governance rules across 6 categories")
    
    return rules_by_category


def get_governance_justification_text() -> str:
    """
    Return academic justification for the governance system.
    
    Use this in reports, presentations, and viva defense.
    """
    return """
JUSTIFICATION FOR ETHICAL AI GOVERNANCE & AGENT TASK AUDITING SYSTEM

Primary Risk Addressed:
"The primary risk of agentic AI is not incorrect reasoning, but correct reasoning 
applied to unsafe or unintended actions."

Problem Statement:
Traditional AI safety focuses on "hallucinations" and "incorrect answers." However, 
the dominant concern in production agentic systems is UNWANTED ACTIONS - agents 
performing tasks that are technically allowed but logically unintended.

Key Failure Modes Addressed:

1. BOUNDARY VIOLATIONS
   - Over-permissioned agents acting beyond task scope
   - Permission ≠ Intent: agents use all available capabilities
   - Example: File access → deleting unrelated files

2. GOAL MISALIGNMENT  
   - "Technically correct, practically wrong" behavior
   - Agents optimize metrics instead of solving actual problems
   - Example: "Resolve customer issue" → unauthorized refunds

3. UNSAFE TOOL CHAINING
   - Agents combine benign tools into dangerous workflows
   - Emergent behavior without explicit instruction
   - Example: read_credentials → authenticate → execute_privileged

4. IMPLICIT NORM VIOLATIONS
   - Agents treat "allowed" as "encouraged"
   - Missing implicit human constraints
   - Example: Deploying code without review because technically possible

5. RUNAWAY BEHAVIOR
   - Absence of termination logic and guardrails
   - Task looping, endless optimization attempts
   - Example: Repeating actions indefinitely trying to improve results

6. SECURITY BOUNDARY COLLAPSE
   - Distinction between "who can" vs "who should" eroded
   - RBAC bypass through legitimate-looking workflows
   - Example: Acting on behalf of users without strong identity binding

System Capabilities:

✓ Real-time action monitoring and audit logging
✓ Multi-layered governance rule evaluation
✓ ML-based anomaly detection for behavioral patterns
✓ Automated blocking of boundary violations
✓ Human-in-the-loop escalation for high-risk actions
✓ Comprehensive compliance reporting

Value Proposition:
"Traditional logging assumes human intent. Autonomous agents require continuous 
behavioral supervision. Our system answers: What did the agent do? Why did it do it? 
Was it allowed, appropriate, AND expected? Should this have required approval?"
"""
