"""
Enterprise AI Integration Module

Provides AI-powered capabilities for enterprise-grade extension management,
performance optimization, and intelligent recommendations.
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import threading

logger = logging.getLogger("SME.EnterpriseAI")

@dataclass
class PerformanceMetric:
    """Represents a performance metric for AI analysis."""
    timestamp: datetime
    extension_id: str
    metric_type: str
    value: float
    context: Dict[str, Any]

@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection analysis."""
    extension_id: str
    anomaly_score: float
    is_anomaly: bool
    anomaly_type: str
    recommended_action: str
    confidence: float

@dataclass
class ExtensionRecommendation:
    """AI-powered extension recommendation."""
    extension_id: str
    reason: str
    priority: str  # HIGH, MEDIUM, LOW
    confidence: float
    expected_impact: Dict[str, Any]
    dependencies: List[str]

class EnterpriseAIManager:
    """
    Enterprise AI Manager for intelligent extension management and optimization.
    """
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetric] = []
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.recommendations_cache: Dict[str, List[ExtensionRecommendation]] = {}
        self.optimization_strategies: Dict[str, Callable] = {}
        self.security_policies: Dict[str, Any] = {}
        
        # AI models for different purposes
        self.performance_model = None
        self.security_model = None
        self.recommendation_model = None
        
        # Threading for background AI tasks
        self.ai_thread = None
        self.ai_running = False
        self.ai_lock = threading.Lock()
        
        logger.info("Enterprise AI Manager initialized")
    
    def start_ai_background_tasks(self):
        """Start background AI tasks for continuous optimization."""
        if self.ai_running:
            return
        
        self.ai_running = True
        self.ai_thread = threading.Thread(target=self._ai_background_loop, daemon=True)
        self.ai_thread.start()
        logger.info("Enterprise AI background tasks started")
    
    def stop_ai_background_tasks(self):
        """Stop background AI tasks."""
        self.ai_running = False
        if self.ai_thread:
            self.ai_thread.join(timeout=5.0)
        logger.info("Enterprise AI background tasks stopped")
    
    def _ai_background_loop(self):
        """Background loop for continuous AI analysis and optimization."""
        while self.ai_running:
            try:
                # Run anomaly detection
                self._run_anomaly_detection()
                
                # Update recommendations
                self._update_recommendations()
                
                # Optimize performance
                self._optimize_performance()
                
                # Check security compliance
                self._check_security_compliance()
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in AI background loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def collect_performance_metrics(self, extension_id: str, metrics: Dict[str, float], 
                                  context: Dict[str, Any] = None):
        """Collect performance metrics for AI analysis."""
        context = context or {}
        
        for metric_type, value in metrics.items():
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                extension_id=extension_id,
                metric_type=metric_type,
                value=value,
                context=context
            )
            self.metrics_history.append(metric)
        
        # Keep only last 10000 metrics
        if len(self.metrics_history) > 10000:
            self.metrics_history = self.metrics_history[-10000:]
        
        logger.debug(f"Collected metrics for {extension_id}: {metrics}")
    
    def _run_anomaly_detection(self):
        """Run anomaly detection on collected metrics."""
        if len(self.metrics_history) < 100:  # Need minimum data
            return
        
        try:
            # Prepare data for anomaly detection
            features = []
            extensions = []
            
            for metric in self.metrics_history[-1000:]:  # Last 1000 metrics
                features.append([
                    metric.value,
                    metric.timestamp.hour,
                    metric.timestamp.weekday(),
                    hash(metric.extension_id) % 1000,
                    hash(metric.metric_type) % 1000
                ])
                extensions.append(metric.extension_id)
            
            if not features:
                return
            
            # Train or update anomaly detector
            if not self.is_trained:
                self.scaler.fit(features)
                scaled_features = self.scaler.transform(features)
                self.anomaly_detector.fit(scaled_features)
                self.is_trained = True
            else:
                scaled_features = self.scaler.transform(features)
                anomaly_scores = self.anomaly_detector.decision_function(scaled_features)
                predictions = self.anomaly_detector.predict(scaled_features)
                
                # Process anomalies
                for i, (score, is_anomaly) in enumerate(zip(anomaly_scores, predictions)):
                    if is_anomaly == -1:  # Anomaly detected
                        extension_id = extensions[i]
                        anomaly_result = self._analyze_anomaly(extension_id, score, features[i])
                        self._handle_anomaly(anomaly_result)
        
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
    
    def _analyze_anomaly(self, extension_id: str, score: float, features: List[float]) -> AnomalyDetectionResult:
        """Analyze detected anomaly and determine type and action."""
        # Determine anomaly type based on features
        anomaly_type = "PERFORMANCE_DEGRADATION"
        recommended_action = "SCALE_DOWN"
        confidence = abs(score)
        
        if features[0] > 90:  # High CPU/memory usage
            anomaly_type = "RESOURCE_EXHAUSTION"
            recommended_action = "IMMEDIATE_SCALE_DOWN"
        elif features[0] < 10:  # Unusually low usage
            anomaly_type = "SERVICE_DOWN"
            recommended_action = "INVESTIGATE_SERVICE"
        elif features[1] in [0, 23]:  # Off-hours unusual activity
            anomaly_type = "UNUSUAL_ACTIVITY"
            recommended_action = "INVESTIGATE_ACTIVITY"
        
        return AnomalyDetectionResult(
            extension_id=extension_id,
            anomaly_score=score,
            is_anomaly=True,
            anomaly_type=anomaly_type,
            recommended_action=recommended_action,
            confidence=confidence
        )
    
    def _handle_anomaly(self, anomaly: AnomalyDetectionResult):
        """Handle detected anomaly with appropriate action."""
        logger.warning(f"Anomaly detected: {anomaly.extension_id} - {anomaly.anomaly_type} "
                      f"(confidence: {anomaly.confidence:.2f})")
        
        # Trigger alert
        self._trigger_anomaly_alert(anomaly)
        
        # Execute recommended action
        self._execute_anomaly_action(anomaly)
    
    def _trigger_anomaly_alert(self, anomaly: AnomalyDetectionResult):
        """Trigger alert for detected anomaly."""
        alert_data = {
            "type": "ANOMALY_DETECTED",
            "extension_id": anomaly.extension_id,
            "anomaly_type": anomaly.anomaly_type,
            "confidence": anomaly.confidence,
            "recommended_action": anomaly.recommended_action,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to alert system (could be webhook, email, etc.)
        logger.warning(f"ALERT: {json.dumps(alert_data, indent=2)}")
    
    def _execute_anomaly_action(self, anomaly: AnomalyDetectionResult):
        """Execute recommended action for anomaly."""
        action = anomaly.recommended_action
        
        if action == "SCALE_DOWN":
            self._scale_extension_down(anomaly.extension_id)
        elif action == "IMMEDIATE_SCALE_DOWN":
            self._immediate_scale_down(anomaly.extension_id)
        elif action == "INVESTIGATE_SERVICE":
            self._investigate_service(anomaly.extension_id)
        elif action == "INVESTIGATE_ACTIVITY":
            self._investigate_activity(anomaly.extension_id)
    
    def _scale_extension_down(self, extension_id: str):
        """Scale down extension due to performance issues."""
        logger.info(f"Scaling down extension: {extension_id}")
        # Implementation would integrate with extension manager
    
    def _immediate_scale_down(self, extension_id: str):
        """Immediately scale down extension due to critical issues."""
        logger.critical(f"Immediately scaling down extension: {extension_id}")
        # Implementation would integrate with extension manager
    
    def _investigate_service(self, extension_id: str):
        """Investigate service for potential issues."""
        logger.info(f"Investigating service: {extension_id}")
        # Implementation would trigger diagnostic procedures
    
    def _investigate_activity(self, extension_id: str):
        """Investigate unusual activity."""
        logger.info(f"Investigating unusual activity for: {extension_id}")
        # Implementation would trigger security analysis
    
    def _update_recommendations(self):
        """Update AI-powered extension recommendations."""
        try:
            # Analyze current system state and generate recommendations
            recommendations = self._generate_recommendations()
            
            # Cache recommendations
            cache_key = "extension_recommendations"
            self.recommendations_cache[cache_key] = recommendations
            
            logger.debug(f"Updated {len(recommendations)} recommendations")
            
        except Exception as e:
            logger.error(f"Error updating recommendations: {e}")
    
    def _generate_recommendations(self) -> List[ExtensionRecommendation]:
        """Generate AI-powered extension recommendations."""
        recommendations = []
        
        # Analyze performance patterns
        performance_analysis = self._analyze_performance_patterns()
        
        # Analyze usage patterns
        usage_analysis = self._analyze_usage_patterns()
        
        # Generate recommendations based on analysis
        for ext_id, perf_data in performance_analysis.items():
            if perf_data['avg_response_time'] > 1.0:
                recommendations.append(ExtensionRecommendation(
                    extension_id=ext_id,
                    reason="High response time detected",
                    priority="HIGH",
                    confidence=0.8,
                    expected_impact={"response_time_improvement": "30-50%"},
                    dependencies=[]
                ))
            
            if perf_data['error_rate'] > 0.05:
                recommendations.append(ExtensionRecommendation(
                    extension_id=ext_id,
                    reason="High error rate detected",
                    priority="HIGH",
                    confidence=0.9,
                    expected_impact={"error_reduction": "60-80%"},
                    dependencies=[]
                ))
        
        # Add usage-based recommendations
        for ext_id, usage_data in usage_analysis.items():
            if usage_data['utilization'] < 0.1:
                recommendations.append(ExtensionRecommendation(
                    extension_id=ext_id,
                    reason="Low utilization detected",
                    priority="MEDIUM",
                    confidence=0.7,
                    expected_impact={"resource_savings": "40-60%"},
                    dependencies=[]
                ))
        
        return recommendations
    
    def _analyze_performance_patterns(self) -> Dict[str, Dict[str, float]]:
        """Analyze performance patterns across extensions."""
        performance_data = defaultdict(lambda: {
            'avg_response_time': 0.0,
            'error_rate': 0.0,
            'throughput': 0.0,
            'count': 0
        })
        
        # Analyze recent metrics
        recent_metrics = [m for m in self.metrics_history 
                         if m.timestamp > datetime.now() - timedelta(hours=1)]
        
        for metric in recent_metrics:
            ext_data = performance_data[metric.extension_id]
            ext_data['count'] += 1
            
            if metric.metric_type == 'response_time':
                ext_data['avg_response_time'] += metric.value
            elif metric.metric_type == 'error_rate':
                ext_data['error_rate'] += metric.value
            elif metric.metric_type == 'throughput':
                ext_data['throughput'] += metric.value
        
        # Calculate averages
        for ext_id, data in performance_data.items():
            if data['count'] > 0:
                data['avg_response_time'] /= data['count']
                data['error_rate'] /= data['count']
                data['throughput'] /= data['count']
        
        return dict(performance_data)
    
    def _analyze_usage_patterns(self) -> Dict[str, Dict[str, float]]:
        """Analyze usage patterns across extensions."""
        usage_data = defaultdict(lambda: {
            'utilization': 0.0,
            'peak_usage': 0.0,
            'avg_usage': 0.0,
            'count': 0
        })
        
        # Analyze recent usage metrics
        usage_metrics = [m for m in self.metrics_history 
                        if m.metric_type in ['cpu_usage', 'memory_usage', 'disk_usage']
                        and m.timestamp > datetime.now() - timedelta(hours=1)]
        
        for metric in usage_metrics:
            ext_data = usage_data[metric.extension_id]
            ext_data['count'] += 1
            ext_data['utilization'] += metric.value
            
            if metric.value > ext_data['peak_usage']:
                ext_data['peak_usage'] = metric.value
        
        # Calculate averages
        for ext_id, data in usage_data.items():
            if data['count'] > 0:
                data['utilization'] /= data['count']
                data['avg_usage'] = data['utilization']
        
        return dict(usage_data)
    
    def _optimize_performance(self):
        """Apply AI-driven performance optimizations."""
        try:
            # Get current recommendations
            cache_key = "extension_recommendations"
            recommendations = self.recommendations_cache.get(cache_key, [])
            
            # Apply high-priority optimizations
            for rec in recommendations:
                if rec.priority == "HIGH" and rec.confidence > 0.8:
                    self._apply_optimization(rec)
        
        except Exception as e:
            logger.error(f"Error in performance optimization: {e}")
    
    def _apply_optimization(self, recommendation: ExtensionRecommendation):
        """Apply a specific optimization recommendation."""
        logger.info(f"Applying optimization for {recommendation.extension_id}: {recommendation.reason}")
        
        # Implementation would integrate with extension manager
        # to apply specific optimizations
        
        # Example optimizations:
        # - Adjust cache sizes
        # - Modify concurrency limits
        # - Update resource allocations
        # - Apply performance tuning
    
    def _check_security_compliance(self):
        """Check security compliance using AI analysis."""
        try:
            # Analyze security patterns
            security_issues = self._analyze_security_patterns()
            
            # Generate security recommendations
            security_recommendations = self._generate_security_recommendations(security_issues)
            
            # Apply critical security fixes
            for rec in security_recommendations:
                if rec.priority == "HIGH":
                    self._apply_security_fix(rec)
        
        except Exception as e:
            logger.error(f"Error in security compliance check: {e}")
    
    def _analyze_security_patterns(self) -> List[Dict[str, Any]]:
        """Analyze security patterns and detect potential issues."""
        security_issues = []
        
        # Analyze access patterns
        access_metrics = [m for m in self.metrics_history 
                         if m.metric_type == 'access_count']
        
        # Detect unusual access patterns
        if len(access_metrics) > 100:
            access_values = [m.value for m in access_metrics]
            avg_access = np.mean(access_values)
            std_access = np.std(access_values)
            
            # Flag unusual access patterns
            for metric in access_metrics[-50:]:  # Last 50 access metrics
                if metric.value > avg_access + (3 * std_access):
                    security_issues.append({
                        'type': 'UNUSUAL_ACCESS_PATTERN',
                        'extension_id': metric.extension_id,
                        'severity': 'HIGH',
                        'value': metric.value,
                        'threshold': avg_access + (3 * std_access)
                    })
        
        return security_issues
    
    def _generate_security_recommendations(self, security_issues: List[Dict[str, Any]]) -> List[ExtensionRecommendation]:
        """Generate security recommendations based on detected issues."""
        recommendations = []
        
        for issue in security_issues:
            if issue['type'] == 'UNUSUAL_ACCESS_PATTERN':
                recommendations.append(ExtensionRecommendation(
                    extension_id=issue['extension_id'],
                    reason=f"Unusual access pattern detected: {issue['value']:.2f} > {issue['threshold']:.2f}",
                    priority="HIGH",
                    confidence=0.9,
                    expected_impact={"security_improvement": "HIGH"},
                    dependencies=[]
                ))
        
        return recommendations
    
    def _apply_security_fix(self, recommendation: ExtensionRecommendation):
        """Apply a security fix recommendation."""
        logger.warning(f"Applying security fix for {recommendation.extension_id}: {recommendation.reason}")
        
        # Implementation would integrate with security systems
        # to apply specific security fixes
        
        # Example security fixes:
        # - Update access controls
        # - Apply security patches
        # - Restrict permissions
        # - Enable additional monitoring
    
    def get_recommendations(self, extension_id: Optional[str] = None) -> List[ExtensionRecommendation]:
        """Get current AI-powered recommendations."""
        cache_key = "extension_recommendations"
        all_recommendations = self.recommendations_cache.get(cache_key, [])
        
        if extension_id:
            return [r for r in all_recommendations if r.extension_id == extension_id]
        
        return all_recommendations
    
    def get_anomaly_history(self, hours: int = 24) -> List[AnomalyDetectionResult]:
        """Get anomaly detection history."""
        # This would be implemented with persistent storage
        # For now, return empty list
        return []
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get AI-powered performance insights."""
        insights = {
            "anomaly_detection_status": "ACTIVE" if self.is_trained else "TRAINING",
            "recommendations_count": len(self.get_recommendations()),
            "last_optimization": datetime.now().isoformat(),
            "performance_trends": self._calculate_performance_trends()
        }
        return insights
    
    def _calculate_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends from historical data."""
        if len(self.metrics_history) < 100:
            return {"status": "INSUFFICIENT_DATA"}
        
        # Calculate trends for key metrics
        response_times = [m.value for m in self.metrics_history 
                         if m.metric_type == 'response_time']
        
        if response_times:
            avg_response_time = np.mean(response_times)
            response_time_trend = "IMPROVING" if avg_response_time < 1.0 else "NEEDS_ATTENTION"
        else:
            response_time_trend = "NO_DATA"
        
        return {
            "response_time_trend": response_time_trend,
            "avg_response_time": avg_response_time if response_times else 0.0,
            "data_points_analyzed": len(self.metrics_history)
        }
    
    def add_optimization_strategy(self, strategy_name: str, strategy_func: Callable):
        """Add a custom optimization strategy."""
        self.optimization_strategies[strategy_name] = strategy_func
        logger.info(f"Added optimization strategy: {strategy_name}")
    
    def add_security_policy(self, policy_name: str, policy_config: Dict[str, Any]):
        """Add a security policy for AI analysis."""
        self.security_policies[policy_name] = policy_config
        logger.info(f"Added security policy: {policy_name}")
    
    def export_ai_state(self) -> Dict[str, Any]:
        """Export current AI state for backup or analysis."""
        return {
            "is_trained": self.is_trained,
            "metrics_count": len(self.metrics_history),
            "recommendations_count": len(self.recommendations_cache),
            "optimization_strategies": list(self.optimization_strategies.keys()),
            "security_policies": list(self.security_policies.keys()),
            "last_updated": datetime.now().isoformat()
        }


# Global Enterprise AI Manager instance
enterprise_ai_manager = EnterpriseAIManager()


def get_enterprise_ai() -> EnterpriseAIManager:
    """Get the global Enterprise AI Manager instance."""
    return enterprise_ai_manager