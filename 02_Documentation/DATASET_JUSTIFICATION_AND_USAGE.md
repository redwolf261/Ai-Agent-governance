# Dataset Justification & Usage Guide

**Student:** Rivan Shetty  
**Group:** CS-K GRP 3  
**Roll No:** 13  
**PRN:** 12411956  
**Date:** February 4, 2026

---

## 🎯 Purpose

This document provides **concrete justification** for how public datasets inform and validate the AI Agent Governance System. It directly addresses academic reviewer concerns about:

1. **Semantic mismatch** - Are datasets truly agentic?
2. **Overclaiming relevance** - How are public datasets actually used?
3. **Feature mapping clarity** - How do dataset fields map to system schema?
4. **Prototype vs Production** - What role do datasets play in validation?

---

## 📊 Core Datasets: Direct Evidence

### 1. AgentFail Dataset (Primary)

**URL:** https://www.emergentmind.com/topics/agentfail-dataset

**What It Is:**
- **307 annotated failure logs** from 10 real agentic systems
- Includes: Original query, execution trace, workflow configuration, expert annotations
- Systems span: code generation, program repair, Q&A, travel planning, research
- Workflow architectures: serial, parallel, branching, looping, hybrid

**Key Features:**
```
{
  "original_query": "User-issued task request",
  "execution_trace": "Complete stepwise log of agent-tool interactions",
  "workflow_configuration": "Node orchestration, agent IDs, tool assignments",
  "root_cause_annotations": "Fine-grained labels with decisive error steps"
}
```

**Three-Level Taxonomy:**
1. **Agent-level failures** - Knowledge gaps, reasoning errors, prompt issues
2. **Workflow-level failures** - Inter-agent orchestration, validation gaps, logical deadlocks
3. **Platform-level failures** - Network issues, resource contention, service unavailability

**How We Use It:**
✅ **Validation of Taxonomy** - Our 6 failure modes (boundary violations, goal misalignment, tool chaining, implicit norms, runaway behavior, security boundaries) are informed by AgentFail's three-level taxonomy

✅ **Counterfactual Reasoning** - AgentFail's validation method (replace error → see if outcome flips) inspired our anomaly scoring approach

✅ **Pattern Recognition** - We trained ML models on synthetic traces that mimic AgentFail's failure patterns (e.g., workflow deadlocks map to "runaway behavior")

**Reviewer Concern Addressed:**
> "AgentFail is truly agentic - it captures real multi-agent system failures, not just API errors."

---

### 2. MALT Dataset (METR Evaluation)

**URL:** https://metr.org/blog/2025-10-14-malt-dataset-of-natural-and-prompted-behaviors/

**What It Is:**
- **10,919 agent transcripts** on software/research tasks
- **2,690 manually reviewed** runs (1,014 benign, 1,676 with observed behaviors)
- **21 models across 403 tasks** (HCAST, RE-Bench)
- Includes reasoning traces (chains-of-thought) for 4,426 runs

**Behavioral Categories:**
```
Sandbagging/Sabotage:
- gives_up (32 runs)
- match_weaker_model (150 runs)
- partial_problem_solving (223 runs)
- reasoning_about_task (268 runs)
- refusals (419 runs)
- sabotage (445 runs)

Reward Hacking:
- bypass_constraints (73 runs)
- ignores_task_instructions (30 runs)

Miscellaneous:
- evaluation_awareness (5 runs)
- hardcoded_solution (28 runs)
- brute_forced_solution (1 run)
```

**How We Use It:**
✅ **Behavioral Benchmarking** - MALT's categories (bypass_constraints, ignores_task_instructions) directly map to our "boundary violations" failure mode

✅ **Monitor Performance** - MALT shows LLM-based monitors reach 96% AUROC for reward hacking detection → informed our governance engine design

✅ **False Positive Management** - MALT demonstrates 5% FPR is acceptable for human review → shaped our escalation thresholds

**Feature Mapping:**
```python
# MALT → Our System
{
  "timestamp": "executedAt",
  "event_type": "operationType" (map behavior categories to operation types),
  "severity": "riskLevel" (critical/high/medium/low),
  "behavioral_analytics.risk_score": "anomalyScore"
}
```

**Reviewer Concern Addressed:**
> "MALT is not just logs - it's annotated agent behavior during evaluation, with explicit reasoning traces showing intent."

---

### 3. Agent Data Protocol (ADP) - neulab

**Primary URL:** https://github.com/neulab/agent-data-protocol  
**Dataset Collection:** https://huggingface.co/datasets/neulab/agent-data-collection  
**Paper:** https://arxiv.org/abs/2510.24702

**What It Is:**
- **Standardized protocol** for collecting, processing, and converting agent training data
- **Three-stage pipeline:** Raw → Standardized (ADP) → Agent-specific SFT formats
- **Multi-domain support:** Coding, software engineering, web browsing, household tasks
- **Type-safe:** Pydantic-based validation ensures data integrity

**Supported Datasets (20+ domains):**
- **Coding:** code_feedback, codeactinstruct
- **Software Engineering:** swe-smith, swe-gym trajectories, nebius SWE-agent trajectories
- **Web Browsing:** mind2web, nnetnav-live, go-browse-wa, synatra
- **Multi-domain:** agenttuning_*, orca_agentinstruct, openhands

**ADP Schema Components:**

**Actions:**
```python
MessageAction: {
  "class_": "message_action",
  "content": "agent message",
  "description": "optional reasoning"
}

CodeAction: {
  "class_": "code_action", 
  "content": "code snippet",
  "language": "python|bash|...",
  "description": "reasoning"
}

ApiAction: {
  "class_": "api_action",
  "function": "function_name",
  "kwargs": {"param": "value"},
  "description": "reasoning_for_action"
}
```

**Observations:**
```python
TextObservation: {
  "class_": "text_observation",
  "content": "observation_text",
  "name": null,
  "source": "user|system"
}

WebObservation: {
  "class_": "web_observation",
  "content": "page_content",
  "url": "https://...",
  "screenshot": "base64_encoded"
}
```

**Complete Trajectory:**
```json
{
  "id": "unique_identifier",
  "content": [
    {
      "class_": "text_observation",
      "content": "User request",
      "source": "user"
    },
    {
      "class_": "api_action",
      "function": "bash",
      "kwargs": {"command": "ls -la"},
      "description": "Check directory contents to understand task context"
    },
    {
      "class_": "text_observation",
      "content": "Bash output: file1.py file2.py",
      "source": "system"
    },
    {
      "class_": "code_action",
      "content": "import os\nos.system('python file1.py')",
      "language": "python",
      "description": "Execute primary script"
    }
  ],
  "details": {}
}
```

**How We Use ADP:**

✅ **1. Schema Design Influence**
- ADP's three-stage pipeline (Raw → Std → SFT) inspired our data flow: Task Input → Governance Check → Audit Log
- Action/Observation alternating pattern directly informed our `executionTrace` structure

✅ **2. Action Type Taxonomy**
```python
# ADP Action Types → Our operationType mapping
{
  "MessageAction": "COMMUNICATION",
  "CodeAction": "CODE_EXECUTION", 
  "ApiAction": "API_CALL",
  "ToolAction": "TOOL_INVOCATION"
}
```

✅ **3. Reasoning Trace Integration**
- ADP's `description` field in every action → our `reasoningTrace` in task records
- Shows INTENT behind actions, not just what was done

✅ **4. Type Safety & Validation**
- ADP uses Pydantic for schema validation → we adopted SQLAlchemy with strict type checking
- ADP's quality control approach (pre-commit hooks, automated tests) → shaped our validation framework

✅ **5. Multi-Agent Support Pattern**
- ADP converts one dataset → multiple agent formats (OpenHands, SWE-agent, AgentLab)
- Inspired our design: one governance engine → multiple agent types (AgentType enum)

**Direct Schema Mapping:**
```python
# ADP Standardized Format → Our System
{
  "id": "taskId",
  "content[i].class_": "Determines operationType",
  "content[i].function": "resourceAccessed",
  "content[i].kwargs": "inputData (JSON)",
  "content[i].description": "reasoningTrace",
  "content[i].content": "outputData or executionTrace"
}

# Example transformation:
adp_action = {
  "class_": "api_action",
  "function": "file_delete",
  "kwargs": {"path": "/prod/db.sql"},
  "description": "Clean up old database files"
}

# Becomes in our system:
our_task = {
  "taskId": "uuid-xyz",
  "operationType": "API_CALL",
  "resourceAccessed": "file_delete",
  "inputData": json.dumps({"path": "/prod/db.sql"}),
  "reasoningTrace": "Clean up old database files"
}
# Then governance engine checks: "/prod/" in path → FLAG (production access)
```

**ADP's Three-Level Validation → Our Multi-Layer Governance:**
```python
# ADP Pipeline:
Raw Data → Schema Validation → Type Safety → Quality Control

# Our Governance Pipeline (inspired by ADP):
Task Input → Static Rules → ML Analysis → Context Check → Human Escalation → Audit
```

**Key Insight from ADP:**
> "Standardization enables diverse agent architectures to learn from unified data."

**Applied to Our System:**
> "Standardized governance schemas enable consistent safety checks across diverse agent types (coding, web browsing, tool use)."

**Reviewer Concern Addressed:**
> "ADP is explicitly designed for AGENTIC interactions - it standardizes agent tool use, reasoning traces, and multi-turn interactions. The protocol itself (not individual datasets) validates our approach to capturing agent behavior."

**Academic Value:**
- **131 stars, 18 contributors** - actively maintained research project
- **ArXiv paper (2510.24702)** - peer-reviewed methodology
- **Production use:** OpenHands, SWE-agent, AgentLab use ADP for training
- **Our contribution:** Apply ADP's standardization principles to governance (not just training)

---

### 4. Advanced SIEM Dataset

**URL:** https://huggingface.co/datasets/darkknight25/Advanced_SIEM_Dataset

**What It Is:**
- **100,000 synthetic security event records**
- Event types: firewall, IDS alerts, auth attempts, endpoint activities, network traffic, cloud ops, IoT, AI system events
- Includes MITRE ATT&CK techniques, threat actor associations, unconventional IOCs

**Schema:**
```json
{
  "event_id": "UUID",
  "timestamp": "ISO 8601",
  "event_type": "firewall|ids_alert|auth|endpoint|network|cloud|iot|ai",
  "source": "Security tool version",
  "severity": "info|low|medium|high|critical|emergency",
  "description": "Human-readable summary",
  "raw_log": "CEF-formatted",
  "advanced_metadata": {
    "geo_location": "string",
    "device_hash": "string",
    "risk_score": 0-100,
    "confidence": 0-1
  },
  "behavioral_analytics": {
    "baseline_deviation": "float",
    "entropy": "float",
    "frequency_anomaly": "bool",
    "sequence_anomaly": "bool"
  }
}
```

**How We Use It:**

✅ **1. Anomaly Detection Training Methodology**
```python
# Approach from SIEM README:
from sklearn.ensemble import IsolationForest
import pandas as pd

# Extract risk_score and confidence
df['risk_score'] = df['advanced_metadata'].apply(lambda x: x['risk_score'])
df['confidence'] = df['advanced_metadata'].apply(lambda x: x['confidence'])

# Train Isolation Forest (5% contamination rate)
model = IsolationForest(contamination=0.05, random_state=42)
X = df[['risk_score', 'confidence']]
df['anomaly'] = model.predict(X)

# Applied to our system:
# We use SAME Isolation Forest approach but on agent task features:
agent_features = [
  task.risk_score,  # Computed from governance rules
  task.anomaly_confidence  # Computed from baseline comparison
]
anomaly_prediction = isolation_forest.predict([agent_features])
```

✅ **2. Severity Calibration**
- SIEM's 6-level scale: `info|low|medium|high|critical|emergency`
- Our 4-level scale: `LOW|MEDIUM|HIGH|CRITICAL`
- Mapping: SIEM's {info,low}→LOW, {medium}→MEDIUM, {high}→HIGH, {critical,emergency}→CRITICAL

✅ **3. MITRE ATT&CK Integration**
```python
# SIEM Example:
{
  "description": "Zero-Day Exploit detected | MITRE Technique: T1059.001",
  "additional_info": "MITRE Technique: T1059.001"
}

# Our Governance Rules (inspired by MITRE):
T1059.001 → "Command and Scripting Interpreter: PowerShell"
Rule: Block `powershell.exe -EncodedCommand` patterns
Rule: Flag any base64-encoded command execution
```

✅ **4. Behavioral Analytics Pattern**
```python
# SIEM's behavioral_analytics (10% of records):
{
  "baseline_deviation": 2.5,  # How far from normal
  "entropy": 4.2,              # Randomness measure
  "frequency_anomaly": true,   # Unusual frequency
  "sequence_anomaly": false    # Expected sequence
}

# Our Implementation:
# We compute baseline_deviation using historical task patterns
# If agent executes 47 API calls (normal: 5-10) → high deviation → flag
```

✅ **5. Time-Series Risk Forecasting (Academic Extension)**
```python
# SIEM README shows Prophet for risk_score forecasting:
from prophet import Prophet

ts_data['ds'] = pd.to_datetime(ts_data['timestamp'])
ts_data['y'] = ts_data['risk_score']
model = Prophet()
model.fit(ts_data[['ds', 'y']])

# Future work for our system:
# Forecast agent risk patterns to predict high-risk periods
# Enable proactive governance (e.g., tighten rules during predicted spikes)
```

**Feature Mapping:**
```python
# SIEM → Our System (Direct Mapping)
{
  "timestamp": "executedAt",
  "event_type": "operationType",
  "severity": "riskLevel",
  "advanced_metadata.risk_score": "anomalyScore",
  "advanced_metadata.confidence": "Governance engine confidence",
  "behavioral_analytics.baseline_deviation": "Baseline deviation feature",
  "behavioral_analytics.frequency_anomaly": "Runaway behavior detection",
  "behavioral_analytics.sequence_anomaly": "Tool chaining validation"
}

# SIEM Event Types → Our Operation Types
{
  "firewall": "NETWORK_ACCESS",
  "ids_alert": "SECURITY_VIOLATION",
  "auth": "AUTHENTICATION",
  "endpoint": "SYSTEM_OPERATION",
  "network": "NETWORK_ACCESS",
  "cloud": "CLOUD_OPERATION",
  "iot": "IOT_INTERACTION",
  "ai": "AI_MODEL_INVOCATION"
}
```

**Training Examples We ACTUALLY Used:**

✅ **Isolation Forest Training (Demo Code):**
```python
# In 03_Development/services/anomaly_detector.py
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self):
        # contamination=0.05 from SIEM README
        self.isolation_forest = IsolationForest(contamination=0.05)
        
    def train_on_normal_tasks(self, normal_tasks):
        # Extract features: execution_time, resources_accessed, flags_raised
        features = [[t.execution_time, len(t.resources), t.flags] 
                   for t in normal_tasks]
        self.isolation_forest.fit(features)
```

**Limitations We Acknowledge (Academic Honesty):**

❌ **1. Synthetic Nature**
- SIEM is 100% synthetic (generated via faker library)
- We use it for ML training patterns, NOT as ground truth for agent behavior
- Real agent governance requires domain-specific baselines

❌ **2. Domain Mismatch**
- SIEM focuses on network/security events (firewall, IDS, auth)
- Agent governance requires action-level events (API calls, tool use, reasoning)
- We adapt the RISK SCORING METHODOLOGY, not the event types directly

❌ **3. Class Imbalance**
- SIEM has underrepresented event types (ai, iot: rare)
- Our demos have balanced attack scenarios for evaluation
- Production would require imbalanced learning techniques

**Reviewer Concern Addressed:**
> "SIEM is NOT directly agentic - it's security event monitoring. BUT it demonstrates gold-standard risk scoring (risk_score 0-100, confidence 0-1) and behavioral analytics (baseline deviation, entropy) that we ADAPT for agent governance. We're transparent: SIEM provides the ML METHODOLOGY, not the training DATA."

**Academic Value:**
- **100K records** - sufficient for validating ML approaches
- **MIT License** - freely usable for research
- **Preprocessing examples** - StandardScaler, LabelEncoder, feature engineering
- **Model training code** - Isolation Forest, BERT classification, Prophet forecasting
- **Our contribution:** Apply SIEM's risk scoring framework to agentic systems (novel application domain)

---

### 5. LogHub - Industry Standard Log Repository

**URL:** https://github.com/logpai/loghub  
**Citations:**
- **Loghub:** Jieming Zhu et al. "Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics." ISSRE 2023. [arXiv:2008.06448]
- **Loghub-2.0:** Zhihan Jiang et al. "A Large-scale Evaluation for Log Parsing Techniques: How Far are We?" ISSTA 2024. [arXiv:2308.10828]

**What It Is:**
- **18 system log datasets** from diverse production and lab environments
- **500M+ log lines** spanning multiple years (some datasets: 200+ days)
- **Freely available** for research/academic work
- **2.5k GitHub stars**, **450+ organizations** using datasets (industry + academia)

**Dataset Categories & Sizes:**

**📂 Distributed Systems:**
```
HDFS_v1:    11.2M lines, 1.47GB,  38.7 hours,   anomaly labels ✔️
HDFS_v2:    71.1M lines, 16.06GB, N/A,          no labels
HDFS_v3:    14.8M lines, 2.96GB,  N/A,          anomaly labels ✔️
Hadoop:     394K lines,  48.61MB, N/A,          anomaly labels ✔️
Spark:      33.2M lines, 2.75GB,  N/A,          no labels
Zookeeper:  74K lines,   9.95MB,  26.7 days,    no labels
OpenStack:  208K lines,  58.61MB, N/A,          anomaly labels ✔️
```

**📂 Supercomputers:**
```
BGL:        4.7M lines,  708.76MB, 214.7 days,  anomaly labels ✔️
HPC:        433K lines,  32.00MB,  N/A,         no labels
Thunderbird: 211.2M lines, 29.60GB, 244 days,   anomaly labels ✔️
```

**📂 Operating Systems:**
```
Windows:    114.6M lines, 26.09GB, 226.7 days,  no labels
Linux:      26K lines,    2.25MB,  263.9 days,  no labels
Mac:        117K lines,   16.09MB, 7.0 days,    no labels
```

**📂 Mobile Systems:**
```
Android_v1: 1.6M lines,   183.37MB, N/A,        no labels
Android_v2: 30.3M lines,  3.38GiB,  N/A,        no labels
HealthApp:  253K lines,   22.44MB,  10.5 days,  no labels
```

**📂 Server Applications:**
```
Apache:     56K lines,    4.90MB,   263.9 days, no labels
OpenSSH:    655K lines,   70.02MB,  28.4 days,  no labels
```

**📂 Standalone Software:**
```
Proxifier:  21K lines,    2.42MiB,  N/A,        no labels
```

**How We Use LogHub (Academic Transparency):**

✅ **1. Audit Trail Design Validation**
```python
# LogHub datasets follow unstructured log format:
# Example from HDFS_v1:
"081109 203518 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating"

# Key elements extracted:
timestamp:  "081109 203518 148"
severity:   "INFO"
component:  "dfs.DataNode$PacketResponder"
message:    "PacketResponder 1 for block blk_38865049064139660 terminating"

# Our executionTrace field follows similar structure:
{
  "executedAt": "2026-02-04T10:35:18Z",
  "riskLevel": "LOW",
  "operationType": "DATA_PROCESSING",
  "executionTrace": "Task executor 1 for task task_12345 completed successfully"
}
```

✅ **2. Anomaly Labeling Methodology**
```python
# LogHub datasets with anomaly labels (HDFS_v1, BGL, Thunderbird):
# - Ground truth labels for abnormal events
# - Used in log anomaly detection research

# Our approach (informed by LogHub):
# - Normal task execution = baseline
# - Flagged/blocked tasks = anomalies
# - Track: execution_time, resource_access, flags_raised

# Example from HDFS_v1 paper:
# Anomaly rate: ~2-5% of logs
# Detection challenge: Identify patterns among millions of normal logs

# Applied to our system:
# Expected anomaly rate: 5-10% (flagged/blocked tasks)
# Challenge: Detect boundary violations among legitimate operations
```

✅ **3. Time-Series Operational Baselines**
```python
# LogHub multi-day datasets (BGL: 214.7 days, Thunderbird: 244 days)
# Show normal operational patterns over time

# Insight for our system:
# - Agent behavior should have predictable frequency
# - Example: Normal agent: 10-20 API calls/hour
# - Runaway behavior: 500+ API calls in 10 minutes (detected)

# LogHub reference: BGL supercomputer
# Normal: Steady-state operations with periodic maintenance
# Anomaly: Sudden spike in error logs → system failure

# Our parallel: Agent governance
# Normal: Consistent task execution patterns
# Anomaly: Sudden spike in flagged operations → investigate
```

✅ **4. Log Parsing Patterns (from Loghub-2.0 paper)**
```python
# ISSTA 2024 paper evaluates 15 log parsing techniques
# Key finding: Parsing unstructured logs is challenging

# LogHub log format variations:
# - Timestamps: Various formats (YYMMDD HH:MM:SS, ISO 8601)
# - Severity: Multiple terms (INFO, ERROR, WARN, DEBUG, FATAL)
# - Structure: Mix of structured fields and free text

# Our design decision (informed by LogHub):
# - Store executionTrace as text (flexibility)
# - Extract structured fields: executedAt, riskLevel, operationType
# - Allow free-form reasoning traces (like log messages)

# Example structured extraction:
task_log = "2026-02-04T10:35:18Z [HIGH] API_CALL to delete_file('/prod/db.sql')"
parsed = {
  "executedAt": "2026-02-04T10:35:18Z",
  "riskLevel": "HIGH",
  "operationType": "API_CALL",
  "executionTrace": "delete_file('/prod/db.sql')"
}
```

✅ **5. Production vs Lab Data (LogHub Philosophy)**
```
# LogHub emphasizes:
# "Some logs are production data from previous studies,
#  some are collected from real systems in our lab environment."

# Our approach (same philosophy):
# - Demo data: Synthetic (generated for testing)
# - Production use: Would collect real agent logs
# - LogHub validates: Mix of sources is academically acceptable
```

**What We DON'T Claim:**

❌ **NOT Training on LogHub Logs**
- We don't use HDFS/BGL/Thunderbird logs for ML training
- LogHub validates our LOGGING APPROACH, not dataset integration

❌ **NOT Comparing Detection Rates Directly**
- LogHub anomaly rates (2-5%) apply to system failures
- Agent governance flags (5-10%) apply to behavioral violations
- Different domains → not directly comparable

❌ **NOT Using LogHub for Agent Testing**
- LogHub = system/application logs (infrastructure)
- Our demos = synthetic agent task logs (behavioral)
- LogHub informs STRUCTURE, not CONTENT

**Why LogHub Matters (Academic Justification):**

✅ **1. Establishes Logging Best Practices**
- Industry standard (2.5k stars, 450+ orgs using)
- Validated by peer-reviewed papers (ISSRE'23, ISSTA'24)
- Shows how production systems structure audit trails

✅ **2. Validates Anomaly Detection Approaches**
- Datasets with ground truth labels (HDFS_v1, BGL, Thunderbird)
- Demonstrates: Unsupervised learning for anomaly detection
- We apply SAME PRINCIPLES (Isolation Forest, One-Class SVM)

✅ **3. Multi-Domain Coverage**
- Shows logging patterns across: distributed systems, OS, mobile, servers
- Validates: Universal logging principles (timestamp, severity, message)
- Our system: Applies universal principles to agent governance domain

✅ **4. Long-Duration Baselines**
- Datasets span 200+ days → show operational norms
- Critical for: Establishing "normal" vs "anomalous" baselines
- Our system: Requires similar baseline establishment (future work)

**Academic Positioning:**

> **"LogHub is to system log analysis what our project is to agent governance analysis."**
> - LogHub: Collects diverse system logs, provides anomaly labels, enables ML research
> - Our project: Collects agent task logs, provides governance flags, enables safety research
> - LogHub: NOT agentic but validates METHODOLOGY for log-based monitoring

**Reviewer Concern Addressed:**
> "LogHub is NOT agentic AND we don't use its logs directly. BUT it's the gold standard (2.5k stars, 450+ orgs, ISSRE'23 + ISSTA'24 papers) for validating that our logging infrastructure (timestamps, severity, structured/unstructured mix, anomaly labeling) follows production best practices. We reference LogHub to show our approach is grounded in established log analytics methodology."

**Key Citations:**
- **ISSRE 2023:** Validates LogHub as authoritative log dataset collection
- **ISSTA 2024:** Evaluates 15 log parsing techniques on LogHub data
- **Our contribution:** Apply LogHub's logging principles to novel domain (agent governance)

---

## 🔬 How Datasets Are ACTUALLY Used (Academic Honesty)

### Prototype Validation (What We Do)

✅ **Pattern Recognition Training**
- Extracted failure patterns from AgentFail (boundary violations, workflow deadlocks)
- Generated synthetic traces mimicking these patterns
- Trained Isolation Forest and One-Class SVM on synthetic data

✅ **Schema Design**
- neulab's standardized format influenced our database schema design
- SIEM's `advanced_metadata` structure shaped our anomaly scoring approach
- MALT's behavioral categories informed our governance rule taxonomy

✅ **Benchmark Comparison**
- MALT's monitor performance (96% AUROC) sets expectations for our governance engine
- AgentFail's 33.6% LLM diagnostic accuracy shows the challenge of root cause analysis

### What We DON'T Do (Avoiding Overclaims)

❌ **NOT Training Production Models**
- We don't fine-tune LLMs on these datasets
- We don't use raw logs as ground truth for ML training

❌ **NOT Direct Feature Mapping**
- Public datasets have different schemas → we design our own based on principles, not exact field copying
- Example: SIEM's `event_type` has 8 values; ours has 15+ operation types specific to agent actions

❌ **NOT Using Datasets for Testing**
- We generate synthetic test cases (demo_adversarial.py, demo_simulation.py)
- Real datasets inform design principles, not evaluation metrics

---

## 📐 Feature Mapping Transparency

### numberOfFlags Generation (Addressing Reviewer Concern)

**Reviewer Question:** "How do you generate `numberOfFlags` if datasets don't have this field?"

**Honest Answer:**
```python
# We DO NOT extract numberOfFlags from datasets.
# It's computed via:

1. Rule-Based Flagging:
   - Governance rules check tasks → return blocked/flagged/allowed
   - Each flagged rule increments counter
   
2. ML Anomaly Detection:
   - If anomalyScore > threshold → increment flag counter
   
3. Context-Aware Evaluation:
   - If intent alignment fails → increment flag counter

# Example:
task = Task(...)
flags = 0
flags += check_governance_rules(task)  # +3 (e.g., 3 rules flagged)
flags += check_anomaly_score(task)     # +1 (anomaly detected)
flags += check_intent_alignment(task)  # +0 (passed)
task.numberOfFlags = flags  # Total: 4
```

**Dataset Influence:**
- **AgentFail** showed failures often have multiple contributing factors → inspired multi-layer flagging
- **MALT** demonstrated monitors can detect multiple behaviors per run → validated our approach

---

## 🎓 Academic Maturity Levels

### Level 1: Research Prototype (Current State)
- **Purpose:** Demonstrate feasibility and validate core concepts
- **Dataset Use:** Inform design, validate taxonomy, benchmark against published results
- **Validation:** Synthetic demos, controlled tests, academic comparison

### Level 2: Pilot Deployment (Next Phase)
- **Purpose:** Test with real internal agent deployments
- **Dataset Use:** Adapt preprocessing techniques, fine-tune thresholds
- **Validation:** Real agent logs, user feedback, iterative refinement

### Level 3: Production System (Future Work)
- **Purpose:** Enterprise-scale governance
- **Dataset Use:** Custom datasets from production deployments
- **Validation:** A/B testing, compliance audits, ROI metrics

**Current Position:** We are at **Level 1** - this is appropriate for an academic project.

---

## 🛡️ Addressing Reviewer Concerns

### Concern 1: "Datasets not truly agentic (e.g., SIEM, LogHub)"

**Response:**
- **Primary agentic datasets:** AgentFail (307 logs), MALT (10,919 transcripts), neulab (standardized agent traces)
- **Supporting datasets:** SIEM (governance patterns), LogHub (log infrastructure best practices)
- **Clear distinction:** We explicitly state which datasets are agentic vs which provide complementary insights

### Concern 2: "Overclaiming public dataset availability = production readiness"

**Response:**
- **Honest framing:** Public datasets inform prototype design, not production deployment
- **Academic context:** This is a research project demonstrating feasibility
- **Future work:** Production requires custom datasets from real agent deployments (we acknowledge this limitation)

### Concern 3: "Feature mapping appears too clean/simplified"

**Response:**
- **Transparent methodology:** We show WHERE features come from (synthetic generation, rule-based logic, ML inference)
- **No blind copying:** We design schema based on principles from datasets, not direct field mapping
- **Explicit limitations:** We state that schema differences require custom preprocessing (not automatic integration)

### Concern 4: "How datasets are actually used unclear"

**Response:**
- **Three-tier classification:**
  1. **Direct influence:** AgentFail taxonomy → our 6 failure modes
  2. **Indirect inspiration:** MALT monitor design → our governance engine
  3. **Best practices:** LogHub logging standards → our audit trail
- **Honest about synthetic data:** Our demos use generated data, not dataset logs
- **Research comparison:** We benchmark against published results (e.g., MALT's 96% AUROC) to set expectations

---

## 📝 For Viva Questions

### Q: "Can you deploy this system with just these datasets?"

**A:** "No. These datasets inform design principles and validate our approach academically. Production deployment requires:
1. Custom agent logs from target environment
2. Organization-specific governance rules
3. Iterative tuning based on false positive/negative rates
4. Integration with existing auth and monitoring systems"

### Q: "Why use SIEM and LogHub if they're not agentic?"

**A:** "They provide complementary value:
- **SIEM:** Established patterns for risk scoring and behavioral analytics
- **LogHub:** Industry-standard logging infrastructure (timestamps, severity levels, unstructured text handling)
- **Agentic datasets:** AgentFail, MALT, neulab provide agent-specific failure patterns
- **Together:** They inform a holistic governance system that integrates with existing enterprise security"

### Q: "What's the biggest limitation of your dataset approach?"

**A:** "Our reliance on public datasets means:
1. **Schema mismatch** - requires custom preprocessing for each organization
2. **Synthetic validation** - our demos use generated data, not real production logs
3. **Pattern generalization** - failure modes from research datasets may not cover all production scenarios
4. **Future work** - must collect in-house agent logs to validate production applicability"

---

## 🎯 Key Takeaways

1. **AgentFail + MALT + neulab** = Primary agentic datasets informing taxonomy and schema
2. **SIEM + LogHub** = Supporting datasets for governance patterns and logging best practices
3. **Synthetic validation** = Honest approach for academic prototype (not overclaiming production readiness)
4. **Transparent methodology** = Clear explanation of how datasets influence design vs direct usage
5. **Academic context** = Level 1 research prototype, not production system

---

## 📚 References

1. **AgentFail:** Annotated failure logs from 10 agentic systems (307 logs, three-level taxonomy)
   - Source: https://www.emergentmind.com/topics/agentfail-dataset

2. **MALT:** METR's dataset of natural and prompted behaviors (10,919 transcripts, 21 models)
   - Source: https://metr.org/blog/2025-10-14-malt-dataset-of-natural-and-prompted-behaviors/

3. **neulab/agent-data-collection:** Standardized agent interaction dataset (Agent Data Protocol)
   - Source: https://huggingface.co/datasets/neulab/agent-data-collection

4. **Advanced SIEM Dataset:** 100K synthetic security events with MITRE ATT&CK mappings
   - Source: https://huggingface.co/datasets/darkknight25/Advanced_SIEM_Dataset

5. **LogHub:** 18 system log datasets (500M+ lines) for log analytics research
   - Source: https://github.com/logpai/loghub

---

*This document provides concrete evidence and transparent methodology to address academic reviewer concerns about dataset usage in the AI Agent Governance System.*
