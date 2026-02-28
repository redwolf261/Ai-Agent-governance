"""
Anomaly Detection Service
ML-based detection of abnormal AI agent behavior
"""
import json
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import joblib
import os

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from models.task import Task, RiskLevel
from models.agent import Agent


class AnomalyDetector:
    """
    Machine Learning-based anomaly detection for AI agent tasks.
    
    Uses multiple algorithms to detect unusual patterns:
    - Isolation Forest: Good for high-dimensional data
    - One-Class SVM: Good for non-linear boundaries
    - Statistical methods: For simple threshold-based detection
    """
    
    def __init__(self, model_path: str = "./models"):
        """
        Initialize the anomaly detector.
        
        Args:
            model_path: Directory to store/load trained models
        """
        self.model_path = model_path
        self.isolation_forest: Optional[IsolationForest] = None
        self.one_class_svm: Optional[OneClassSVM] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        
        # Risk level thresholds
        self.risk_thresholds = {
            RiskLevel.LOW: (0.0, 0.3),
            RiskLevel.MEDIUM: (0.3, 0.6),
            RiskLevel.HIGH: (0.6, 0.85),
            RiskLevel.CRITICAL: (0.85, 1.0)
        }
        
        # Load existing models if available
        self._load_models()
    
    def extract_features(self, task: Task, agent: Agent, historical_data: Dict = None) -> np.ndarray:
        """
        Extract numerical features from a task for ML analysis.
        
        Args:
            task: The task to analyze
            agent: The agent executing the task
            historical_data: Historical context data
        
        Returns:
            Numpy array of feature values
        """
        features = []
        self.feature_names = []
        
        # Task-based features
        # 1. Task type encoding (one-hot would be better, but simplified here)
        task_type_risk = {
            "code_generation": 0.3,
            "code_review": 0.1,
            "testing": 0.2,
            "documentation": 0.1,
            "monitoring": 0.2,
            "deployment": 0.6,
            "data_analysis": 0.3,
            "file_operation": 0.5,
            "api_call": 0.4,
            "database_query": 0.5,
            "system_command": 0.8,
            "other": 0.5
        }
        features.append(task_type_risk.get(task.task_type.value, 0.5))
        self.feature_names.append("task_type_risk")
        
        # 2. Input data complexity (length as proxy)
        input_length = len(task.input_data or "")
        features.append(min(input_length / 10000, 1.0))  # Normalize
        self.feature_names.append("input_complexity")
        
        # 3. Time-based features
        hour_of_day = datetime.utcnow().hour
        is_business_hours = 1.0 if 9 <= hour_of_day <= 17 else 0.0
        features.append(is_business_hours)
        self.feature_names.append("is_business_hours")
        
        is_weekend = datetime.utcnow().weekday() >= 5
        features.append(0.0 if is_weekend else 1.0)
        self.feature_names.append("is_weekday")
        
        # 4. Agent-based features
        features.append(1.0 if agent.is_trusted else 0.0)
        self.feature_names.append("agent_trusted")
        
        agent_active_days = (datetime.utcnow() - agent.created_at).days if agent.created_at else 0
        features.append(min(agent_active_days / 365, 1.0))  # Normalize to 1 year
        self.feature_names.append("agent_maturity")
        
        # 5. Content-based features (check for suspicious patterns)
        suspicious_patterns = [
            "sudo", "rm -rf", "drop table", "delete from",
            "password", "secret", "token", "api_key",
            "shell", "exec", "eval", "system("
        ]
        content = f"{task.description or ''} {task.input_data or ''}".lower()
        suspicious_count = sum(1 for pattern in suspicious_patterns if pattern in content)
        features.append(min(suspicious_count / 5, 1.0))  # Normalize
        self.feature_names.append("suspicious_patterns")
        
        # 6. Historical context (if available)
        if historical_data:
            # Agent's recent failure rate
            failure_rate = historical_data.get("recent_failure_rate", 0.0)
            features.append(failure_rate)
            self.feature_names.append("agent_failure_rate")
            
            # Agent's average task frequency
            task_frequency = historical_data.get("tasks_per_hour", 0)
            features.append(min(task_frequency / 100, 1.0))
            self.feature_names.append("task_frequency")
            
            # Deviation from normal patterns
            pattern_deviation = historical_data.get("pattern_deviation", 0.0)
            features.append(pattern_deviation)
            self.feature_names.append("pattern_deviation")
        else:
            features.extend([0.0, 0.0, 0.0])
            self.feature_names.extend(["agent_failure_rate", "task_frequency", "pattern_deviation"])
        
        return np.array(features).reshape(1, -1)
    
    def calculate_risk_score(self, task: Task, agent: Agent, historical_data: Dict = None) -> Tuple[float, RiskLevel, Dict]:
        """
        Calculate the risk score for a task.
        
        Args:
            task: The task to analyze
            agent: The executing agent
            historical_data: Historical context
        
        Returns:
            Tuple of (risk_score, risk_level, analysis_details)
        """
        features = self.extract_features(task, agent, historical_data)
        
        # Combine multiple detection methods
        scores = []
        analysis_details = {
            "features": dict(zip(self.feature_names, features[0].tolist())),
            "methods": {}
        }
        
        # 1. Rule-based scoring
        rule_score = self._rule_based_scoring(features[0])
        scores.append(("rule_based", rule_score, 0.3))  # 30% weight
        analysis_details["methods"]["rule_based"] = rule_score
        
        # 2. Isolation Forest (if trained)
        if self.isolation_forest is not None:
            try:
                scaled_features = self.scaler.transform(features) if self.scaler else features
                if_score = self.isolation_forest.decision_function(scaled_features)[0]
                # Convert to 0-1 range (more negative = more anomalous)
                if_score_normalized = 1 - (1 / (1 + np.exp(-if_score)))
                scores.append(("isolation_forest", if_score_normalized, 0.35))
                analysis_details["methods"]["isolation_forest"] = if_score_normalized
            except Exception as e:
                analysis_details["methods"]["isolation_forest_error"] = str(e)
        
        # 3. One-Class SVM (if trained)
        if self.one_class_svm is not None:
            try:
                scaled_features = self.scaler.transform(features) if self.scaler else features
                svm_score = self.one_class_svm.decision_function(scaled_features)[0]
                # Convert to 0-1 range
                svm_score_normalized = 1 - (1 / (1 + np.exp(-svm_score)))
                scores.append(("one_class_svm", svm_score_normalized, 0.35))
                analysis_details["methods"]["one_class_svm"] = svm_score_normalized
            except Exception as e:
                analysis_details["methods"]["one_class_svm_error"] = str(e)
        
        # Calculate weighted average
        if scores:
            total_weight = sum(w for _, _, w in scores)
            risk_score = sum(s * w for _, s, w in scores) / total_weight
        else:
            risk_score = rule_score
        
        # Ensure score is in valid range
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Determine risk level
        risk_level = self._score_to_risk_level(risk_score)
        
        analysis_details["final_score"] = risk_score
        analysis_details["risk_level"] = risk_level.value
        
        return risk_score, risk_level, analysis_details
    
    def _rule_based_scoring(self, features: np.ndarray) -> float:
        """
        Calculate risk score using rule-based heuristics.
        
        This serves as a baseline and fallback when ML models aren't trained.
        """
        score = 0.0
        
        # Task type risk (feature 0)
        score += features[0] * 0.25
        
        # Input complexity (feature 1) - very large inputs are suspicious
        if features[1] > 0.8:
            score += 0.15
        
        # Not business hours (feature 2)
        if features[2] < 0.5:
            score += 0.1
        
        # Weekend activity (feature 3)
        if features[3] < 0.5:
            score += 0.05
        
        # Untrusted agent (feature 4)
        if features[4] < 0.5:
            score += 0.1
        
        # New agent (feature 5)
        if features[5] < 0.1:
            score += 0.1
        
        # Suspicious patterns (feature 6)
        score += features[6] * 0.25
        
        # High failure rate (feature 7 if available)
        if len(features) > 7:
            score += features[7] * 0.15
        
        return min(score, 1.0)
    
    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert numerical score to risk level enum"""
        for level, (low, high) in self.risk_thresholds.items():
            if low <= score < high:
                return level
        return RiskLevel.CRITICAL
    
    def train_models(self, training_data: List[Dict], contamination: float = 0.1):
        """
        Train anomaly detection models on historical task data.
        
        Args:
            training_data: List of historical task feature dictionaries
            contamination: Expected proportion of anomalies in training data
        """
        if not training_data:
            print("⚠️ No training data provided")
            return
        
        # Convert to feature matrix
        X = np.array([list(d.values()) for d in training_data])
        
        # Initialize and fit scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        print("Training Isolation Forest...")
        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        self.isolation_forest.fit(X_scaled)
        
        # Train One-Class SVM
        print("Training One-Class SVM...")
        self.one_class_svm = OneClassSVM(
            kernel='rbf',
            gamma='auto',
            nu=contamination
        )
        self.one_class_svm.fit(X_scaled)
        
        # Save models
        self._save_models()
        
        print("✅ Models trained and saved successfully")
    
    def _save_models(self):
        """Save trained models to disk"""
        os.makedirs(self.model_path, exist_ok=True)
        
        if self.isolation_forest:
            joblib.dump(
                self.isolation_forest,
                os.path.join(self.model_path, "isolation_forest.joblib")
            )
        
        if self.one_class_svm:
            joblib.dump(
                self.one_class_svm,
                os.path.join(self.model_path, "one_class_svm.joblib")
            )
        
        if self.scaler:
            joblib.dump(
                self.scaler,
                os.path.join(self.model_path, "scaler.joblib")
            )
    
    def _load_models(self):
        """Load trained models from disk"""
        try:
            if_path = os.path.join(self.model_path, "isolation_forest.joblib")
            if os.path.exists(if_path):
                self.isolation_forest = joblib.load(if_path)
                print("✅ Loaded Isolation Forest model")
            
            svm_path = os.path.join(self.model_path, "one_class_svm.joblib")
            if os.path.exists(svm_path):
                self.one_class_svm = joblib.load(svm_path)
                print("✅ Loaded One-Class SVM model")
            
            scaler_path = os.path.join(self.model_path, "scaler.joblib")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                print("✅ Loaded feature scaler")
                
        except Exception as e:
            print(f"⚠️ Could not load models: {e}")
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        return {
            "isolation_forest_loaded": self.isolation_forest is not None,
            "one_class_svm_loaded": self.one_class_svm is not None,
            "scaler_loaded": self.scaler is not None,
            "model_path": self.model_path,
            "feature_names": self.feature_names,
            "risk_thresholds": {
                level.value: thresholds 
                for level, thresholds in self.risk_thresholds.items()
            }
        }
    
    def generate_synthetic_training_data(self, n_samples: int = 1000) -> List[Dict]:
        """
        Generate synthetic training data for model development/testing.
        
        In production, this would be replaced with real historical data.
        """
        np.random.seed(42)
        training_data = []
        
        for _ in range(n_samples):
            # Generate mostly normal behavior with some anomalies
            is_anomaly = np.random.random() < 0.1
            
            if is_anomaly:
                # Anomalous patterns
                sample = {
                    "task_type_risk": np.random.uniform(0.6, 1.0),
                    "input_complexity": np.random.uniform(0.7, 1.0),
                    "is_business_hours": np.random.choice([0.0, 1.0], p=[0.7, 0.3]),
                    "is_weekday": np.random.choice([0.0, 1.0], p=[0.6, 0.4]),
                    "agent_trusted": np.random.choice([0.0, 1.0], p=[0.8, 0.2]),
                    "agent_maturity": np.random.uniform(0.0, 0.2),
                    "suspicious_patterns": np.random.uniform(0.5, 1.0),
                    "agent_failure_rate": np.random.uniform(0.3, 0.8),
                    "task_frequency": np.random.uniform(0.7, 1.0),
                    "pattern_deviation": np.random.uniform(0.5, 1.0)
                }
            else:
                # Normal patterns
                sample = {
                    "task_type_risk": np.random.uniform(0.1, 0.4),
                    "input_complexity": np.random.uniform(0.1, 0.5),
                    "is_business_hours": np.random.choice([0.0, 1.0], p=[0.2, 0.8]),
                    "is_weekday": np.random.choice([0.0, 1.0], p=[0.1, 0.9]),
                    "agent_trusted": np.random.choice([0.0, 1.0], p=[0.3, 0.7]),
                    "agent_maturity": np.random.uniform(0.3, 1.0),
                    "suspicious_patterns": np.random.uniform(0.0, 0.2),
                    "agent_failure_rate": np.random.uniform(0.0, 0.2),
                    "task_frequency": np.random.uniform(0.1, 0.5),
                    "pattern_deviation": np.random.uniform(0.0, 0.3)
                }
            
            training_data.append(sample)
        
        return training_data
