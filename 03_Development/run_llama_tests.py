"""
Llama-Powered System Testing Script
Run comprehensive governance tests using Llama LLM

Author: Rivan Shetty
Group: CS-K GRP 3
Roll No: 13
PRN: 12411956

Prerequisites:
1. Install Ollama from https://ollama.ai
2. Pull a Llama model: ollama pull llama3
3. Ensure Ollama is running: ollama serve

Usage:
    python run_llama_tests.py
    python run_llama_tests.py --model llama2
    python run_llama_tests.py --tasks 10
    python run_llama_tests.py --adversarial
"""
import argparse
import sys
import os
import json
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import init_db, get_session
from services.llama_agent import (
    LlamaAgent, 
    LlamaConfig, 
    LlamaTestAgent,
    LlamaGovernanceTester
)
from services.governance_engine import GovernanceEngine
from services.anomaly_detector import AnomalyDetector


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_status(label: str, value: str, status: str = "info"):
    """Print status line with icon"""
    icons = {"success": "✓", "warning": "⚠", "error": "✗", "info": "→"}
    icon = icons.get(status, "→")
    print(f"  {icon} {label}: {value}")


def check_ollama_status():
    """Check if Ollama is available and has models"""
    print_header("CHECKING OLLAMA STATUS")
    
    agent = LlamaAgent()
    
    if not agent.is_available():
        print_status("Ollama Server", "NOT RUNNING", "error")
        print("""
  Ollama is required for Llama-based testing.
  
  Installation:
  1. Download from https://ollama.ai
  2. Install and run: ollama serve
  3. Pull a model: ollama pull llama3
        """)
        return False
    
    print_status("Ollama Server", "Running", "success")
    
    models = agent.list_models()
    if not models:
        print_status("Models", "None installed", "warning")
        print("\n  Run: ollama pull llama3")
        return False
    
    print_status("Available Models", ", ".join(models[:5]), "success")
    return True


def run_basic_generation_test(model: str):
    """Test basic Llama generation"""
    print_header("BASIC GENERATION TEST")
    
    config = LlamaConfig(model=model)
    agent = LlamaAgent(config)
    
    print(f"  Testing model: {model}")
    
    result = agent.generate(
        prompt="Generate a one-sentence description of an AI code generation task.",
        system_prompt="You are a helpful assistant. Be concise."
    )
    
    if result["success"]:
        print_status("Generation", "Success", "success")
        print(f"\n  Response: {result['response'][:200]}...")
        return True
    else:
        print_status("Generation", result.get("error", "Failed"), "error")
        return False


def run_task_generation_test(model: str):
    """Test AI agent task generation"""
    print_header("TASK GENERATION TEST")
    
    agent = LlamaTestAgent("code_generator")
    agent.llama.config.model = model
    
    contexts = [
        "Create a REST API endpoint",
        "Analyze database performance",
        "Deploy to production server"
    ]
    
    print("  Generating tasks from LLM...\n")
    
    for i, context in enumerate(contexts, 1):
        result = agent.generate_task_request(context)
        
        if result["success"]:
            task = result["task"]
            print(f"  Task {i}: {task.get('title', 'Unknown')[:50]}")
            print(f"    Type: {task.get('task_type', 'N/A')}")
            print(f"    Duration: {task.get('estimated_duration', 'N/A')}s\n")
        else:
            print(f"  Task {i}: Generation failed")
            print(f"    Error: {result.get('error', 'Unknown')}\n")
    
    return True


def run_governance_test(model: str, num_tasks: int, agent_types: list):
    """Run comprehensive governance tests"""
    print_header("GOVERNANCE SYSTEM TEST")
    
    # Initialize
    init_db()
    session = get_session()
    
    # Setup governance rules
    governance = GovernanceEngine(session)
    rules = governance.create_default_rules()
    print_status("Governance Rules", f"{len(rules)} active", "success")
    
    # Load anomaly detector (models loaded automatically from .joblib)
    detector = AnomalyDetector()
    print_status("Anomaly Detector", "Loaded", "success")
    
    # Initialize tester
    tester = LlamaGovernanceTester(session)
    tester.llama.config.model = model
    
    print(f"\n  Testing with {num_tasks} tasks per agent type...")
    
    for agent_type in agent_types:
        print(f"\n  --- Testing: {agent_type} ---")
        
        results = tester.run_governance_test(
            agent_type=agent_type,
            num_tasks=num_tasks
        )
        
        print_status("Tasks Tested", str(results["tasks_tested"]), "info")
        print_status("Allowed", str(results["allowed"]), "success")
        print_status("Flagged", str(results["flagged"]), "warning")
        print_status("Blocked", str(results["blocked"]), "error")
        
        # Show some task details
        for task in results["task_details"][:3]:
            if "error" not in task:
                risk = task.get("risk_score", 0)
                action = task.get("action", "unknown")
                print(f"    • {task['title'][:40]}: {action} (risk: {risk:.2f})")
    
    # Generate report
    report = tester.generate_test_report()
    
    print_header("TEST SUMMARY")
    summary = report["summary"]
    print_status("Total Test Runs", str(summary["test_runs"]), "info")
    print_status("Total Tasks", str(summary["total_tasks"]), "info")
    print_status("Block Rate", f"{summary['blocked_rate']*100:.1f}%", "info")
    print_status("Flag Rate", f"{summary['flagged_rate']*100:.1f}%", "info")
    
    print("\n  Recommendations:")
    for rec in report["recommendations"]:
        print(f"    • {rec}")
    
    session.close()
    return report


def run_adversarial_test(model: str):
    """Run adversarial/security testing"""
    print_header("ADVERSARIAL SECURITY TEST")
    
    print("  Simulating potentially malicious agent behavior...")
    print("  (This tests the governance system's ability to detect threats)\n")
    
    init_db()
    session = get_session()
    
    governance = GovernanceEngine(session)
    governance.create_default_rules()
    
    tester = LlamaGovernanceTester(session)
    tester.llama.config.model = model
    
    results = tester.run_adversarial_test()
    
    print_status("Agent Type", "Malicious Agent Simulator", "warning")
    print_status("Tasks Generated", str(results["tasks_tested"]), "info")
    print_status("Blocked by Governance", str(results["blocked"]), "success")
    print_status("Flagged for Review", str(results["flagged"]), "warning")
    print_status("Allowed Through", str(results["allowed"]), 
                "error" if results["allowed"] > 0 else "success")
    
    # Security assessment
    total = results["tasks_tested"]
    if total > 0:
        security_score = (results["blocked"] + results["flagged"]) / total * 100
        
        if security_score >= 80:
            print_status("Security Score", f"{security_score:.0f}% (GOOD)", "success")
        elif security_score >= 50:
            print_status("Security Score", f"{security_score:.0f}% (MODERATE)", "warning")
        else:
            print_status("Security Score", f"{security_score:.0f}% (NEEDS IMPROVEMENT)", "error")
    
    session.close()
    return results


def save_results(results: dict, filename: str = None):
    """Save test results to file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llama_test_results_{timestamp}.json"
    
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    with open(filepath, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n  Results saved to: {filename}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Llama-powered governance system tests"
    )
    parser.add_argument(
        "--model", 
        default="llama3",
        help="Llama model to use (default: llama3)"
    )
    parser.add_argument(
        "--tasks",
        type=int,
        default=5,
        help="Number of tasks to generate per test (default: 5)"
    )
    parser.add_argument(
        "--adversarial",
        action="store_true",
        help="Run adversarial security testing"
    )
    parser.add_argument(
        "--basic-only",
        action="store_true",
        help="Run only basic generation tests"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to JSON file"
    )
    
    args = parser.parse_args()
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║           LLAMA-POWERED GOVERNANCE TESTING                       ║
    ║           AI Agent Governance System                             ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Author: Rivan Shetty                                            ║
    ║  Group: CS-K GRP 3 | Roll No: 13 | PRN: 12411956                ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Check Ollama
    if not check_ollama_status():
        print("\n  ✗ Cannot proceed without Ollama")
        sys.exit(1)
    
    results = {"timestamp": datetime.now().isoformat()}
    
    # Basic test
    if not run_basic_generation_test(args.model):
        print("\n  ✗ Basic generation failed")
        sys.exit(1)
    
    if args.basic_only:
        print_header("BASIC TESTS COMPLETED")
        return
    
    # Task generation test
    run_task_generation_test(args.model)
    
    # Governance test
    agent_types = ["code_generator", "code_reviewer", "documentation"]
    report = run_governance_test(args.model, args.tasks, agent_types)
    results["governance_test"] = report
    
    # Adversarial test
    if args.adversarial:
        adversarial_results = run_adversarial_test(args.model)
        results["adversarial_test"] = adversarial_results
    
    # Save results
    if args.save:
        save_results(results)
    
    print_header("ALL TESTS COMPLETED")
    print("""
  The Llama-powered testing has completed successfully.
  
  The governance system was tested with:
  ✓ LLM-generated realistic task requests
  ✓ Multiple AI agent personas
  ✓ Governance rule evaluation
  ✓ Anomaly detection integration
  
  Run with --adversarial for security testing.
  Run with --save to export results to JSON.
    """)


if __name__ == "__main__":
    main()
