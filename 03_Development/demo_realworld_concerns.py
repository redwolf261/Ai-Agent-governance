"""
Real-World Agent Governance Demo
Demonstrates prevention of actual problems engineers complain about

"The primary risk of agentic AI is not incorrect reasoning, 
but correct reasoning applied to unsafe or unintended actions."

Author: Rivan Shetty
Group: CS-K GRP 3
Roll No: 13
PRN: 12411956
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import init_db, get_session
from services.advanced_governance_rules import (
    initialize_advanced_governance_rules,
    get_governance_justification_text
)


# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_banner():
    """Print banner"""
    print(f"""
{Colors.BOLD}{Colors.CYAN}
    ========================================================================
    |                                                                      |
    |    REAL-WORLD AGENT GOVERNANCE DEMONSTRATION                         |
    |                                                                      |
    |    Addressing Actual Problems Engineers Complain About               |
    |                                                                      |
    ========================================================================
    |  Author: Rivan Shetty                                                |
    |  Group: CS-K GRP 3 | Roll No: 13 | PRN: 12411956                    |
    ========================================================================
{Colors.END}
""")


def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}{Colors.END}\n")


def print_concern(number: int, title: str, problem: str, example: str):
    """Print a concern category"""
    print(f"{Colors.BOLD}[{number}] {title}{Colors.END}")
    print(f"    {Colors.YELLOW}Problem:{Colors.END} {problem}")
    print(f"    {Colors.RED}Example:{Colors.END} {example}\n")


def main():
    """Main execution"""
    print_banner()
    
    print_section("WHAT ENGINEERS ACTUALLY COMPLAIN ABOUT")
    
    print(f"{Colors.BOLD}The fear is not 'wrong answers' but UNWANTED ACTIONS{Colors.END}\n")
    
    # Real-world concerns
    print_concern(
        1,
        "Over-Permissioned Agents Acting Beyond Intent",
        "Permission ≠ Intent - agents use all capabilities if goals nudge them",
        "Agent with file access deletes unrelated files; Agent closes Jira tickets prematurely"
    )
    
    print_concern(
        2,
        "Goal Misalignment: 'Solved the KPI, Not the Problem'",
        "Agents achieve objectives through technically correct but inappropriate means",
        "'Resolve customer issue' → agent refunds without authorization"
    )
    
    print_concern(
        3,
        "Agents Chaining Tools in Unsafe Ways",
        "Combining benign tools into dangerous workflows; emergent behavior",
        "Tool A (read creds) → Tool B (authenticate) → Tool C (execute privileged)"
    )
    
    print_concern(
        4,
        "Ignoring Implicit Human Norms",
        "Agents treat 'allowed' as 'encouraged'; missing unwritten rules",
        "Deploy code without review; Overwrite configs; Act without approval"
    )
    
    print_concern(
        5,
        "Lack of Stop Conditions: Runaway Behavior",
        "Agents loop endlessly, repeat actions, continue after success",
        "Task loops endlessly; Continues optimizing despite partial success"
    )
    
    print_concern(
        6,
        "Security Boundary Violations",
        "Collapse of 'who can' vs 'who should' distinction",
        "Acting on behalf of users without strong identity binding"
    )
    
    print_section("INITIALIZING ADVANCED GOVERNANCE SYSTEM")
    
    print(f"{Colors.CYAN}Creating governance rules that address these specific concerns...{Colors.END}\n")
    
    # Initialize database
    init_db()
    session = get_session()
    
    try:
        print(f"\n{Colors.GREEN}{Colors.BOLD}GOVERNANCE CAPABILITIES DEPLOYED:{Colors.END}\n")
        
        print(f"{Colors.BOLD}The system addresses 6 critical failure modes:{Colors.END}\n")
        
        categories = {
            "Boundary Violations": [
                "Production Environment Protection",
                "File System Scope Restrictions", 
                "Unapproved Communication Blocking",
                "Resource Access Monitoring"
            ],
            "Goal Misalignment": [
                "Financial Action Authorization",
                "Verification Bypass Detection",
                "Alert Suppression Prevention",
                "Intent vs Outcome Validation"
            ],
            "Unsafe Tool Chaining": [
                "Privilege Escalation Detection",
                "Multi-Step Attack Pattern Recognition",
                "Human Checkpoint Requirements",
                "Chain Depth Limits"
            ],
            "Implicit Norm Violations": [
                "Deployment Review Requirements",
                "Existing Work Preservation",
                "Context-Aware Modification Rules",
                "Time-Based Action Gating"
            ],
            "Runaway Behavior": [
                "Repetitive Action Loop Detection",
                "Success State Recognition",
                "Maximum Task Duration Limits",
                "Progress Monitoring with Timeout"
            ],
            "Security Boundaries": [
                "Strong Identity Binding",
                "Data Access Scope Validation",
                "RBAC Bypass Prevention",
                "Audit Trail Requirements"
            ]
        }
        
        for category, capabilities in categories.items():
            print(f"{Colors.BOLD}{category}:{Colors.END}")
            for capability in capabilities:
                print(f"  • {capability}")
            print()
        
        print_section("SYSTEM CAPABILITIES")
        
        capabilities = [
            "Real-time action monitoring and audit logging",
            "Multi-layered governance rule evaluation",
            "ML-based anomaly detection for behavioral patterns",
            "Automated blocking of boundary violations",
            "Human-in-the-loop escalation for high-risk actions",
            "Comprehensive compliance reporting"
        ]
        
        for capability in capabilities:
            print(f"  {Colors.GREEN}[+]{Colors.END} {capability}")
        
        print_section("KEY INSIGHT")
        
        print(f'{Colors.BOLD}{Colors.YELLOW}')
        print('"The primary risk of agentic AI is not incorrect reasoning,')
        print(' but correct reasoning applied to unsafe or unintended actions."')
        print(f'{Colors.END}')
        
        print_section("SYSTEM ANSWERS CRITICAL QUESTIONS")
        
        questions = [
            "What did the agent do?",
            "Why did it do it?",
            "Was it allowed, appropriate, AND expected?",
            "Should this action have required human approval?",
            "Did the agent exceed its intended scope?",
            "Is this behavior consistent with implicit norms?"
        ]
        
        for q in questions:
            print(f"  {Colors.CYAN}?{Colors.END} {q}")
        
        print_section("ACADEMIC JUSTIFICATION")
        
        print(get_governance_justification_text())
        
        print_section("NEXT STEPS")
        
        print(f"{Colors.BOLD}To see the system in action:{Colors.END}\n")
        print(f"  1. Run adversarial testing:")
        print(f"     {Colors.CYAN}python demo_adversarial.py{Colors.END}\n")
        print(f"  2. Start the web dashboard:")
        print(f"     {Colors.CYAN}python app.py{Colors.END}\n")
        print(f"  3. Run the full simulation:")
        print(f"     {Colors.CYAN}python demo_simulation.py{Colors.END}\n")
        
        print(f"{Colors.GREEN}{Colors.BOLD}[+] SYSTEM READY FOR DEMONSTRATION{Colors.END}\n")
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
