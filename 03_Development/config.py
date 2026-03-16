"""
Configuration Management for AI Agent Governance System
"""
import os
import secrets
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    name: str = os.getenv("DB_NAME", "ai_governance")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "password")
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def sqlite_connection_string(self) -> str:
        """SQLite connection for development/testing"""
        return "sqlite:///ai_governance.db"


@dataclass
class MLConfig:
    """Machine Learning configuration settings"""
    model_path: str = os.getenv("ML_MODEL_PATH", "./models")
    anomaly_threshold: float = float(os.getenv("ANOMALY_THRESHOLD", "0.7"))
    risk_levels: dict = None
    
    def __post_init__(self):
        self.risk_levels = {
            "LOW": (0.0, 0.3),
            "MEDIUM": (0.3, 0.6),
            "HIGH": (0.6, 0.85),
            "CRITICAL": (0.85, 1.0)
        }


@dataclass
class GovernanceConfig:
    """Governance rules configuration"""
    max_execution_time_seconds: int = int(os.getenv("MAX_EXECUTION_TIME", "300"))
    allowed_task_types: list = None
    restricted_operations: list = None
    escalation_enabled: bool = True
    auto_block_critical: bool = True
    
    def __post_init__(self):
        self.allowed_task_types = [
            "code_generation",
            "code_review",
            "testing",
            "documentation",
            "monitoring",
            "deployment",
            "data_analysis"
        ]
        self.restricted_operations = [
            "database_delete",
            "system_shutdown",
            "credential_access",
            "network_modification",
            "file_system_root_access"
        ]


@dataclass
class APIConfig:
    """API configuration settings"""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "5000"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY") or secrets.token_urlsafe(32))
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


@dataclass
class Config:
    """Main configuration class"""
    database: DatabaseConfig = None
    ml: MLConfig = None
    governance: GovernanceConfig = None
    api: APIConfig = None
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    def __post_init__(self):
        self.database = DatabaseConfig()
        self.ml = MLConfig()
        self.governance = GovernanceConfig()
        self.api = APIConfig()


# Global configuration instance
config = Config()
