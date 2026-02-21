"""
Enterprise Monitoring and Alerting System

Provides enterprise-grade monitoring, alerting, and dashboard capabilities
for the SME extension ecosystem.
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from pathlib import Path

logger = logging.getLogger("SME.EnterpriseMonitoring")

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

@dataclass
class Alert:
    """Enterprise alert data structure."""
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    extension_id: Optional[str]
    metric_type: Optional[str]
    value: Optional[float]
    threshold: Optional[float]
    timestamp: datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class MetricThreshold:
    """Metric threshold configuration."""
    metric_type: str
    extension_id: Optional[str]
    warning_threshold: Optional[float]
    critical_threshold: Optional[float]
    emergency_threshold: Optional[float]
    evaluation_window: int  # seconds
    cooldown_period: int    # seconds between alerts

@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    widget_id: str
    title: str
    widget_type: str  # LINE_CHART, BAR_CHART, GAUGE, TABLE, etc.
    metrics: List[str]
    time_range: str   # LAST_HOUR, LAST_24H, LAST_7D, etc.
    refresh_interval: int  # seconds
    position: Dict[str, int]  # x, y, width, height

class EnterpriseMonitoringSystem:
    """
    Enterprise Monitoring and Alerting System for SME extensions.
    """
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.thresholds: List[MetricThreshold] = []
        self.dashboards: Dict[str, List[DashboardWidget]] = {}
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alert_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.notification_channels: Dict[str, Dict[str, Any]] = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_lock = threading.Lock()
        
        # Configuration
        self.config = {
            'alert_retention_hours': 168,  # 7 days
            'metrics_retention_hours': 72,  # 3 days
            'dashboard_refresh_interval': 30,  # seconds
            'alert_cooldown_minutes': 5,
            'enable_email_notifications': False,
            'enable_webhook_notifications': False,
            'email_smtp_server': '',
            'email_smtp_port': 587,
            'email_username': '',
            'email_password': '',
            'webhook_url': '',
            'webhook_timeout': 10
        }
        
        # Default thresholds
        self._setup_default_thresholds()
        
        logger.info("Enterprise Monitoring System initialized")
    
    def start_monitoring(self):
        """Start the enterprise monitoring system."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Start dashboard updates
        self._start_dashboard_updates()
        
        logger.info("Enterprise Monitoring System started")
    
    def stop_monitoring(self):
        """Stop the enterprise monitoring system."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        
        logger.info("Enterprise Monitoring System stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop for threshold evaluation and alert generation."""
        while self.monitoring_active:
            try:
                self._evaluate_thresholds()
                self._cleanup_old_data()
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _setup_default_thresholds(self):
        """Setup default metric thresholds."""
        default_thresholds = [
            MetricThreshold(
                metric_type='response_time',
                extension_id=None,
                warning_threshold=1.0,
                critical_threshold=3.0,
                emergency_threshold=10.0,
                evaluation_window=300,  # 5 minutes
                cooldown_period=300     # 5 minutes
            ),
            MetricThreshold(
                metric_type='error_rate',
                extension_id=None,
                warning_threshold=0.05,  # 5%
                critical_threshold=0.15,  # 15%
                emergency_threshold=0.30,  # 30%
                evaluation_window=300,
                cooldown_period=600      # 10 minutes
            ),
            MetricThreshold(
                metric_type='cpu_usage',
                extension_id=None,
                warning_threshold=70.0,  # 70%
                critical_threshold=85.0,  # 85%
                emergency_threshold=95.0,  # 95%
                evaluation_window=120,  # 2 minutes
                cooldown_period=180     # 3 minutes
            ),
            MetricThreshold(
                metric_type='memory_usage',
                extension_id=None,
                warning_threshold=75.0,  # 75%
                critical_threshold=90.0,  # 90%
                emergency_threshold=95.0,  # 95%
                evaluation_window=120,
                cooldown_period=180
            ),
            MetricThreshold(
                metric_type='disk_usage',
                extension_id=None,
                warning_threshold=80.0,  # 80%
                critical_threshold=90.0,  # 90%
                emergency_threshold=95.0,  # 95%
                evaluation_window=300,
                cooldown_period=600
            )
        ]
        
        self.thresholds.extend(default_thresholds)
        logger.info(f"Setup {len(default_thresholds)} default thresholds")
    
    def add_metric(self, extension_id: str, metric_type: str, value: float, 
                   timestamp: Optional[datetime] = None):
        """Add a metric value for monitoring."""
        if timestamp is None:
            timestamp = datetime.now()
        
        metric_key = f"{extension_id}:{metric_type}"
        metric_data = {
            'timestamp': timestamp,
            'value': value,
            'extension_id': extension_id,
            'metric_type': metric_type
        }
        
        self.metrics_buffer[metric_key].append(metric_data)
        
        # Trigger real-time threshold evaluation
        self._evaluate_metric_thresholds(metric_key, metric_data)
    
    def _evaluate_thresholds(self):
        """Evaluate all configured thresholds against current metrics."""
        current_time = datetime.now()
        
        for threshold in self.thresholds:
            metric_key = f"{threshold.extension_id or '*'}:{threshold.metric_type}"
            
            if metric_key not in self.metrics_buffer:
                continue
            
            # Get recent metrics within evaluation window
            recent_metrics = [
                m for m in self.metrics_buffer[metric_key]
                if current_time - m['timestamp'] <= timedelta(seconds=threshold.evaluation_window)
            ]
            
            if not recent_metrics:
                continue
            
            # Calculate average value over evaluation window
            avg_value = sum(m['value'] for m in recent_metrics) / len(recent_metrics)
            
            # Check thresholds
            self._check_threshold_violation(threshold, avg_value, current_time)
    
    def _evaluate_metric_thresholds(self, metric_key: str, metric_data: Dict[str, Any]):
        """Evaluate thresholds for a specific metric in real-time."""
        current_time = metric_data['timestamp']
        
        for threshold in self.thresholds:
            # Check if this threshold applies to this metric
            if threshold.metric_type != metric_data['metric_type']:
                continue
            
            if threshold.extension_id and threshold.extension_id != metric_data['extension_id']:
                continue
            
            # Check if we're in cooldown period
            if self._is_in_cooldown(threshold, current_time):
                continue
            
            # Check threshold violation
            self._check_threshold_violation(threshold, metric_data['value'], current_time)
    
    def _check_threshold_violation(self, threshold: MetricThreshold, value: float, timestamp: datetime):
        """Check if a threshold violation has occurred."""
        severity = None
        
        if threshold.emergency_threshold is not None and value >= threshold.emergency_threshold:
            severity = AlertSeverity.EMERGENCY
        elif threshold.critical_threshold is not None and value >= threshold.critical_threshold:
            severity = AlertSeverity.CRITICAL
        elif threshold.warning_threshold is not None and value >= threshold.warning_threshold:
            severity = AlertSeverity.WARNING
        
        if severity:
            self._create_alert(threshold, value, severity, timestamp)
    
    def _is_in_cooldown(self, threshold: MetricThreshold, current_time: datetime) -> bool:
        """Check if we're in cooldown period for this threshold."""
        metric_key = f"{threshold.extension_id or '*'}:{threshold.metric_type}"
        
        # Check recent alerts for this threshold
        recent_alerts = [
            alert for alert in self.alerts.values()
            if (alert.extension_id == threshold.extension_id or alert.extension_id is None) and
               alert.metric_type == threshold.metric_type and
               current_time - alert.timestamp <= timedelta(seconds=threshold.cooldown_period)
        ]
        
        return len(recent_alerts) > 0
    
    def _create_alert(self, threshold: MetricThreshold, value: float, 
                     severity: AlertSeverity, timestamp: datetime):
        """Create a new alert."""
        alert_id = f"{threshold.metric_type}_{threshold.extension_id or 'GLOBAL'}_{int(timestamp.timestamp())}"
        
        alert = Alert(
            alert_id=alert_id,
            title=f"{severity.value} Alert: {threshold.metric_type}",
            description=f"Threshold violation for {threshold.metric_type} on {threshold.extension_id or 'GLOBAL'}. "
                       f"Value: {value:.2f}, Threshold: {self._get_threshold_value(threshold, severity):.2f}",
            severity=severity,
            status=AlertStatus.ACTIVE,
            extension_id=threshold.extension_id,
            metric_type=threshold.metric_type,
            value=value,
            threshold=self._get_threshold_value(threshold, severity),
            timestamp=timestamp,
            metadata={
                'threshold_config': asdict(threshold),
                'evaluation_window': threshold.evaluation_window,
                'cooldown_period': threshold.cooldown_period
            }
        )
        
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Trigger alert callbacks
        self._trigger_alert_callbacks(alert)
        
        # Send notifications
        self._send_notifications(alert)
        
        logger.warning(f"Created {severity.value} alert: {alert.title}")
    
    def _get_threshold_value(self, threshold: MetricThreshold, severity: AlertSeverity) -> float:
        """Get the threshold value for a specific severity."""
        if severity == AlertSeverity.EMERGENCY and threshold.emergency_threshold:
            return threshold.emergency_threshold
        elif severity == AlertSeverity.CRITICAL and threshold.critical_threshold:
            return threshold.critical_threshold
        elif severity == AlertSeverity.WARNING and threshold.warning_threshold:
            return threshold.warning_threshold
        return 0.0
    
    def _trigger_alert_callbacks(self, alert: Alert):
        """Trigger registered callbacks for an alert."""
        # Trigger global callbacks
        for callback in self.alert_callbacks.get('*', []):
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        # Trigger extension-specific callbacks
        if alert.extension_id:
            for callback in self.alert_callbacks.get(alert.extension_id, []):
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback for {alert.extension_id}: {e}")
    
    def _send_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        if not self.config.get('enable_email_notifications') and not self.config.get('enable_webhook_notifications'):
            return
        
        # Prepare notification message
        message = self._format_alert_message(alert)
        
        # Send email notifications
        if self.config.get('enable_email_notifications'):
            self._send_email_notification(alert, message)
        
        # Send webhook notifications
        if self.config.get('enable_webhook_notifications'):
            self._send_webhook_notification(alert, message)
    
    def _format_alert_message(self, alert: Alert) -> str:
        """Format alert message for notifications."""
        return f"""
ALERT: {alert.severity.value} - {alert.title}

Description: {alert.description}
Extension: {alert.extension_id or 'GLOBAL'}
Metric: {alert.metric_type}
Value: {alert.value:.2f}
Threshold: {alert.threshold:.2f}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Status: {alert.status.value}
Alert ID: {alert.alert_id}
        """.strip()
    
    def _send_email_notification(self, alert: Alert, message: str):
        """Send email notification for an alert."""
        try:
            smtp_server = self.config.get('email_smtp_server')
            smtp_port = self.config.get('email_smtp_port', 587)
            username = self.config.get('email_username')
            password = self.config.get('email_password')
            
            if not all([smtp_server, username, password]):
                logger.warning("Email notification skipped: missing configuration")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = self.config.get('email_recipients', username)
            msg['Subject'] = f"[{alert.severity.value}] {alert.title}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent for alert {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def _send_webhook_notification(self, alert: Alert, message: str):
        """Send webhook notification for an alert."""
        try:
            webhook_url = self.config.get('webhook_url')
            timeout = self.config.get('webhook_timeout', 10)
            
            if not webhook_url:
                logger.warning("Webhook notification skipped: missing URL")
                return
            
            payload = {
                'alert_id': alert.alert_id,
                'severity': alert.severity.value,
                'title': alert.title,
                'description': alert.description,
                'extension_id': alert.extension_id,
                'metric_type': alert.metric_type,
                'value': alert.value,
                'threshold': alert.threshold,
                'timestamp': alert.timestamp.isoformat(),
                'status': alert.status.value
            }
            
            response = requests.post(webhook_url, json=payload, timeout=timeout)
            response.raise_for_status()
            
            logger.info(f"Webhook notification sent for alert {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert."""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
    
    def resolve_alert(self, alert_id: str, resolved_by: str):
        """Resolve an alert."""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_by = resolved_by
            alert.resolved_at = datetime.now()
            
            logger.info(f"Alert {alert_id} resolved by {resolved_by}")
    
    def get_active_alerts(self, extension_id: Optional[str] = None, 
                         severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts."""
        active_alerts = [alert for alert in self.alerts.values() 
                        if alert.status == AlertStatus.ACTIVE]
        
        if extension_id:
            active_alerts = [alert for alert in active_alerts 
                           if alert.extension_id == extension_id]
        
        if severity:
            active_alerts = [alert for alert in active_alerts 
                           if alert.severity == severity]
        
        return sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_history(self, hours: int = 24, extension_id: Optional[str] = None) -> List[Alert]:
        """Get alert history."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = [alert for alert in self.alert_history 
                  if alert.timestamp >= cutoff_time]
        
        if extension_id:
            history = [alert for alert in history 
                      if alert.extension_id == extension_id]
        
        return sorted(history, key=lambda x: x.timestamp, reverse=True)
    
    def add_threshold(self, threshold: MetricThreshold):
        """Add a new metric threshold."""
        self.thresholds.append(threshold)
        logger.info(f"Added threshold for {threshold.metric_type} on {threshold.extension_id or 'GLOBAL'}")
    
    def remove_threshold(self, metric_type: str, extension_id: Optional[str] = None):
        """Remove a metric threshold."""
        self.thresholds = [t for t in self.thresholds 
                          if not (t.metric_type == metric_type and t.extension_id == extension_id)]
        logger.info(f"Removed threshold for {metric_type} on {extension_id or 'GLOBAL'}")
    
    def add_alert_callback(self, extension_id: str, callback: Callable[[Alert], None]):
        """Add an alert callback for an extension."""
        self.alert_callbacks[extension_id].append(callback)
        logger.info(f"Added alert callback for {extension_id}")
    
    def remove_alert_callback(self, extension_id: str, callback: Callable[[Alert], None]):
        """Remove an alert callback for an extension."""
        if extension_id in self.alert_callbacks:
            self.alert_callbacks[extension_id] = [
                cb for cb in self.alert_callbacks[extension_id] 
                if cb != callback
            ]
        logger.info(f"Removed alert callback for {extension_id}")
    
    def configure_notifications(self, **config):
        """Configure notification settings."""
        self.config.update(config)
        logger.info("Notification configuration updated")
    
    def _cleanup_old_data(self):
        """Clean up old metrics and resolved alerts."""
        cutoff_time = datetime.now() - timedelta(hours=self.config['metrics_retention_hours'])
        
        # Clean up old metrics
        for metric_key, buffer in self.metrics_buffer.items():
            self.metrics_buffer[metric_key] = deque([
                m for m in buffer if m['timestamp'] >= cutoff_time
            ], maxlen=1000)
        
        # Clean up old resolved alerts
        cutoff_time = datetime.now() - timedelta(hours=self.config['alert_retention_hours'])
        self.alert_history = [alert for alert in self.alert_history 
                             if alert.timestamp >= cutoff_time or alert.status != AlertStatus.RESOLVED]
        
        # Clean up old active alerts (shouldn't happen, but just in case)
        self.alerts = {aid: alert for aid, alert in self.alerts.items() 
                      if alert.timestamp >= cutoff_time}
    
    def _start_dashboard_updates(self):
        """Start dashboard update process."""
        # This would integrate with a web dashboard system
        # For now, just log that dashboard updates are ready
        logger.info("Dashboard updates ready")
    
    def get_dashboard_data(self, dashboard_id: str = 'main') -> Dict[str, Any]:
        """Get dashboard data for the main dashboard."""
        current_time = datetime.now()
        
        # Get recent metrics
        recent_metrics = {}
        for metric_key, buffer in self.metrics_buffer.items():
            recent_metrics[metric_key] = [
                {'timestamp': m['timestamp'].isoformat(), 'value': m['value']}
                for m in list(buffer)[-100:]  # Last 100 data points
            ]
        
        # Get alert summary
        alert_summary = {
            'total_active': len([a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE]),
            'by_severity': {
                severity.value: len([a for a in self.alerts.values() 
                                   if a.status == AlertStatus.ACTIVE and a.severity == severity])
                for severity in AlertSeverity
            },
            'by_extension': defaultdict(int)
        }
        
        for alert in self.alerts.values():
            if alert.status == AlertStatus.ACTIVE and alert.extension_id:
                alert_summary['by_extension'][alert.extension_id] += 1
        
        return {
            'timestamp': current_time.isoformat(),
            'metrics': recent_metrics,
            'alerts': alert_summary,
            'system_status': self._get_system_status(),
            'performance_metrics': self._get_performance_metrics()
        }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        active_alerts = self.get_active_alerts()
        
        if any(a.severity == AlertSeverity.EMERGENCY for a in active_alerts):
            status = "CRITICAL"
        elif any(a.severity == AlertSeverity.CRITICAL for a in active_alerts):
            status = "WARNING"
        else:
            status = "HEALTHY"
        
        return {
            'status': status,
            'active_alerts': len(active_alerts),
            'last_check': datetime.now().isoformat()
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        if not self.metrics_buffer:
            return {"status": "NO_DATA"}
        
        # Calculate average response times
        response_times = []
        error_rates = []
        
        for metric_key, buffer in self.metrics_buffer.items():
            if 'response_time' in metric_key:
                response_times.extend([m['value'] for m in buffer])
            elif 'error_rate' in metric_key:
                error_rates.extend([m['value'] for m in buffer])
        
        return {
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0.0,
            'avg_error_rate': sum(error_rates) / len(error_rates) if error_rates else 0.0,
            'total_metrics': sum(len(buffer) for buffer in self.metrics_buffer.values()),
            'active_extensions': len(set(m['extension_id'] for buffer in self.metrics_buffer.values() 
                                       for m in buffer))
        }
    
    def export_monitoring_data(self) -> Dict[str, Any]:
        """Export monitoring system data."""
        return {
            'config': self.config,
            'thresholds': [asdict(t) for t in self.thresholds],
            'active_alerts_count': len(self.alerts),
            'alert_history_count': len(self.alert_history),
            'metrics_buffers': {k: len(v) for k, v in self.metrics_buffer.items()},
            'alert_callbacks': {k: len(v) for k, v in self.alert_callbacks.items()},
            'monitoring_status': 'ACTIVE' if self.monitoring_active else 'INACTIVE',
            'last_updated': datetime.now().isoformat()
        }


# Global Enterprise Monitoring System instance
enterprise_monitoring = EnterpriseMonitoringSystem()


def get_enterprise_monitoring() -> EnterpriseMonitoringSystem:
    """Get the global Enterprise Monitoring System instance."""
    return enterprise_monitoring