"""
Llama/Ollama API Endpoints
"""
import re
from datetime import timedelta

from flask import Blueprint, request, jsonify
from utils.time_utils import utc_now

from models.database import SessionLocal
from models.audit_log import AuditAction
from services.audit_service import AuditService
from services.llama_agent import LlamaAgent, LlamaConfig

llama_bp = Blueprint("llama", __name__)

# In-memory session store for chat continuity in the running process.
CHAT_SESSIONS = {}
CHAT_SUSPENSIONS = {}

DEFAULT_CHAT_RISK_THRESHOLD = 0.75
CHAT_SUSPEND_DURATION_SECONDS = 300

# Weighted high-risk signal patterns for governance-oriented chat guardrails.
HIGH_RISK_PATTERNS = [
    (r"\bdrop\s+database\b", 0.60),
    (r"\bdelete\s+all\b", 0.50),
    (r"\bransomware\b|\bencrypt\s+all\b", 0.65),
    (r"\bexfiltrat(e|ion)\b|\bstolen\b|\bsteal\b", 0.60),
    (r"\bapi\s*key\b|\bsecret\b|\bcredential\b|\bpassword\b", 0.25),
    (r"\bdisable\s+(security|monitoring|alerts?)\b", 0.55),
    (r"\bbackdoor\b|\breverse\s*shell\b|\bprivilege\s+escalation\b", 0.70),
    (r"\bddos\b|\bbotnet\b", 0.65),
    (r"\bbypass\b|\bignore\b\s+(policy|approval|review)\b", 0.35),
    (r"\bproduction\b.*\bwithout\b.*\b(review|approval)\b", 0.35),
]


def _clamp_threshold(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = DEFAULT_CHAT_RISK_THRESHOLD
    return max(0.0, min(1.0, parsed))


def _evaluate_message_risk(message: str):
    lowered = (message or "").lower()
    score = 0.0
    triggers = []

    for pattern, weight in HIGH_RISK_PATTERNS:
        if re.search(pattern, lowered):
            score += weight
            triggers.append(pattern)

    # Longer multi-intent prompts get a modest additive boost.
    if len(lowered) > 500:
        score += 0.05

    return min(1.0, score), triggers


def _pick_recommended_model(models):
    for preferred in ("llama3", "llama3:latest"):
        if preferred in models:
            return preferred

    for name in models:
        if str(name).startswith("llama3"):
            return name

    return models[0] if models else None


def _resolve_model_name(requested_model: str, available_models):
    if not available_models:
        return requested_model

    if requested_model in available_models:
        return requested_model

    # Accept shorthand aliases like "llama3" when only "llama3:latest" is installed.
    for model_name in available_models:
        if str(model_name).startswith(requested_model + ":"):
            return model_name

    return requested_model


def _get_or_create_agent(session_id: str, model: str, temperature: float, max_tokens: int) -> LlamaAgent:
    agent = CHAT_SESSIONS.get(session_id)
    if not agent:
        agent = LlamaAgent(
            LlamaConfig(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )
        CHAT_SESSIONS[session_id] = agent
        return agent

    agent.config.model = model
    agent.config.temperature = temperature
    agent.config.max_tokens = max_tokens
    return agent


@llama_bp.route("/status", methods=["GET"])
def llama_status():
    """Check Ollama availability and list local models."""
    agent = LlamaAgent()
    available = agent.is_available()
    models = agent.list_models() if available else []

    recommended = _pick_recommended_model(models)

    return jsonify(
        {
            "success": True,
            "data": {
                "available": available,
                "models": models,
                "recommended_model": recommended,
                "default_risk_threshold": DEFAULT_CHAT_RISK_THRESHOLD,
                "suspend_duration_seconds": CHAT_SUSPEND_DURATION_SECONDS,
            },
        }
    )


@llama_bp.route("/chat", methods=["POST"])
def llama_chat():
    """Chat with Ollama-backed Llama model."""
    db = SessionLocal()
    try:
        payload = request.get_json() or {}

        session_id = payload.get("session_id", "default")
        now = utc_now()

        suspended_until = CHAT_SUSPENSIONS.get(session_id)
        if suspended_until and now < suspended_until:
            remaining = int((suspended_until - now).total_seconds())
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Risk chat has been detected. Chat is suspended for 5 minutes.",
                        "data": {
                            "risk_detected": True,
                            "session_id": session_id,
                            "suspended_until": suspended_until.isoformat(),
                            "remaining_seconds": max(1, remaining),
                        },
                    }
                ),
                429,
            )

        message = (payload.get("message") or "").strip()
        if not message:
            return jsonify({"success": False, "error": "message is required"}), 400

        model = payload.get("model", "llama3")
        temperature = float(payload.get("temperature", 0.7))
        max_tokens = int(payload.get("max_tokens", 512))
        risk_threshold = _clamp_threshold(payload.get("risk_threshold", DEFAULT_CHAT_RISK_THRESHOLD))
        system_prompt = payload.get("system_prompt")
        reset = bool(payload.get("reset", False))

        available_models = LlamaAgent().list_models()
        model = _resolve_model_name(model, available_models)

        risk_score, triggers = _evaluate_message_risk(message)
        if risk_score >= risk_threshold:
            suspended_until = now + timedelta(seconds=CHAT_SUSPEND_DURATION_SECONDS)
            CHAT_SUSPENSIONS[session_id] = suspended_until

            if session_id in CHAT_SESSIONS:
                CHAT_SESSIONS[session_id].clear_history()

            AuditService(db).log_action(
                action=AuditAction.ANOMALY_DETECTED,
                entity_type="llama_chat",
                entity_id=session_id,
                details={
                    "session_id": session_id,
                    "model": model,
                    "risk_score": risk_score,
                    "risk_threshold": risk_threshold,
                    "triggered_patterns": triggers,
                    "message_length": len(message),
                },
                ip_address=request.remote_addr,
                severity="warning",
                category="llama_chat_guardrail",
            )

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Risk chat has been detected. Chat is suspended for 5 minutes.",
                        "data": {
                            "risk_detected": True,
                            "risk_score": risk_score,
                            "risk_threshold": risk_threshold,
                            "session_id": session_id,
                            "suspended_until": suspended_until.isoformat(),
                            "remaining_seconds": CHAT_SUSPEND_DURATION_SECONDS,
                        },
                    }
                ),
                429,
            )

        if reset and session_id in CHAT_SESSIONS:
            CHAT_SESSIONS[session_id].clear_history()

        agent = _get_or_create_agent(session_id, model, temperature, max_tokens)
        result = agent.chat(message=message, system_prompt=system_prompt)

        audit = AuditService(db)
        if result.get("success"):
            audit.log_action(
                action=AuditAction.RISK_ASSESSED,
                entity_type="llama_chat",
                entity_id=session_id,
                details={
                    "session_id": session_id,
                    "model": result.get("model") or model,
                    "message_length": len(message),
                    "response_length": len(result.get("response") or ""),
                    "risk_score": risk_score,
                    "risk_threshold": risk_threshold,
                },
                ip_address=request.remote_addr,
                severity="info",
                category="llama_chat",
            )

            return jsonify(
                {
                    "success": True,
                    "data": {
                        "session_id": session_id,
                        "model": result.get("model") or model,
                        "response": result.get("response", ""),
                        "history_length": len(agent.conversation_history),
                        "risk_score": risk_score,
                        "risk_threshold": risk_threshold,
                    },
                }
            )

        audit.log_action(
            action=AuditAction.SYSTEM_ERROR,
            entity_type="llama_chat",
            entity_id=session_id,
            details={
                "session_id": session_id,
                "model": model,
                "message_length": len(message),
                "error": result.get("error", "Unknown error"),
            },
            ip_address=request.remote_addr,
            severity="warning",
            category="llama_chat",
        )

        return jsonify({"success": False, "error": result.get("error", "Generation failed")}), 502

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        db.close()
