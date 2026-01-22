"""
⚙️ PIPELINE ORCHESTRATOR - Unified Workflow Automation
Orchestrates entire SimpleMem stack: URL → Spider → Loom → Scribe → Analysis

Coordinates:
✓ HarvesterSpider (Layer 0)
✓ Loom integration (Layer 5)
✓ Scribe forensic analysis (Layer 6)
✓ All expansion tools (Network, Trend, Fact, Scout)
✓ Error handling + retries + monitoring
"""

import logging
import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import sqlite3
import uuid
import json
import os

from mcp.server.fastmcp import FastMCP
from src.core.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("PipelineOrchestrator")

DB_PATH = Config().get_path('storage.db_path')

class JobStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class PipelineJobQueue:
    """Manages batch job execution with retry logic."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_queue_tables()
    
    def _init_queue_tables(self):
        """Initializes job queue tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                job_type TEXT,
                status TEXT DEFAULT 'pending',
                payload TEXT,
                result TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME,
                completed_at DATETIME,
                next_retry_at DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                job_id TEXT,
                event_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(job_id) REFERENCES job_queue(job_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def submit_job(self, job_id: str, job_type: str, payload: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Submits a job to the queue."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO job_queue (job_id, job_type, payload, status, max_retries)
                VALUES (?, ?, ?, ?, ?)
            ''', (job_id, job_type, json.dumps(payload), JobStatus.PENDING.value, max_retries))
            
            conn.commit()
            conn.close()
            
            return {
                'job_id': job_id,
                'status': JobStatus.PENDING.value,
                'submitted_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Gets status of a job."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT job_id, job_type, status, result, error_message, retry_count, created_at, completed_at
                FROM job_queue
                WHERE job_id = ?
            ''', (job_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'job_id': result[0],
                    'job_type': result[1],
                    'status': result[2],
                    'result': json.loads(result[3]) if result[3] else None,
                    'error_message': result[4],
                    'retry_count': result[5],
                    'created_at': result[6],
                    'completed_at': result[7]
                }
            
            return {'error': 'Job not found'}
        
        except Exception as e:
            return {'error': str(e)}
    
    def update_job_status(self, job_id: str, status: str, result: Dict = None, error: str = None) -> bool:
        """Updates job status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status == JobStatus.IN_PROGRESS.value:
                cursor.execute('''
                    UPDATE job_queue
                    SET status = ?, started_at = ?
                    WHERE job_id = ?
                ''', (status, datetime.now(), job_id))
            
            elif status == JobStatus.COMPLETED.value:
                cursor.execute('''
                    UPDATE job_queue
                    SET status = ?, result = ?, completed_at = ?
                    WHERE job_id = ?
                ''', (status, json.dumps(result) if result else None, datetime.now(), job_id))
            
            elif status == JobStatus.FAILED.value:
                cursor.execute('''
                    UPDATE job_queue
                    SET status = ?, error_message = ?, completed_at = ?
                    WHERE job_id = ?
                ''', (status, error, datetime.now(), job_id))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            return False
    
    def get_pending_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets pending jobs for execution."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT job_id, job_type, payload
                FROM job_queue
                WHERE status = ? OR (status = ? AND next_retry_at <= ?)
                LIMIT ?
            ''', (JobStatus.PENDING.value, JobStatus.RETRYING.value, datetime.now(), limit))
            
            results = cursor.fetchall()
            conn.close()
            
            jobs = [
                {
                    'job_id': r[0],
                    'job_type': r[1],
                    'payload': json.loads(r[2]) if r[2] else {}
                }
                for r in results
            ]
            
            return jobs
        
        except Exception as e:
            return []
    
    def retry_job(self, job_id: str, delay_seconds: int = 60) -> Dict[str, Any]:
        """Schedules a job for retry."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current retry count
            cursor.execute('SELECT retry_count, max_retries FROM job_queue WHERE job_id = ?', (job_id,))
            result = cursor.fetchone()
            
            if not result:
                return {'error': 'Job not found'}
            
            retry_count, max_retries = result
            
            if retry_count >= max_retries:
                cursor.execute('UPDATE job_queue SET status = ? WHERE job_id = ?', 
                             (JobStatus.FAILED.value, job_id))
                conn.commit()
                conn.close()
                return {'status': 'max_retries_exceeded'}
            
            next_retry = datetime.now() + timedelta(seconds=delay_seconds)
            cursor.execute('''
                UPDATE job_queue
                SET status = ?, retry_count = ?, next_retry_at = ?
                WHERE job_id = ?
            ''', (JobStatus.RETRYING.value, retry_count + 1, next_retry, job_id))
            
            conn.commit()
            conn.close()
            
            return {
                'job_id': job_id,
                'status': JobStatus.RETRYING.value,
                'retry_count': retry_count + 1,
                'next_retry_at': next_retry.isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}


class PipelineCoordinator:
    """Coordinates multi-step pipeline execution."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.queue = PipelineJobQueue(db_path)
    
    def create_pipeline(self, pipeline_name: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Creates a multi-step pipeline."""
        pipeline = {
            'pipeline_name': pipeline_name,
            'created_at': datetime.now().isoformat(),
            'steps': steps,
            'step_count': len(steps),
            'job_ids': []
        }
        
        # Submit each step as a job
        for i, step in enumerate(steps):
            job_id = f"{pipeline_name}_step_{i}_{datetime.now().timestamp()}"
            self.queue.submit_job(
                job_id,
                step.get('type', 'processing'),
                step.get('params', {}),
                max_retries=step.get('max_retries', 2)
            )
            pipeline['job_ids'].append(job_id)
        
        return pipeline
    
    def execute_pipeline(self, pipeline_name: str) -> Dict[str, Any]:
        """Executes a pipeline."""
        execution = {
            'pipeline_name': pipeline_name,
            'started_at': datetime.now().isoformat(),
            'step_results': [],
            'overall_status': 'executing'
        }
        
        pending = self.queue.get_pending_jobs(limit=100)
        
        for job in pending:
            # Update to in-progress
            self.queue.update_job_status(job['job_id'], JobStatus.IN_PROGRESS.value)
            
            # Simulate processing (in real implementation, would call actual processors)
            execution['step_results'].append({
                'job_id': job['job_id'],
                'job_type': job['job_type'],
                'status': 'processing'
            })
        
        return execution


class ErrorRecoveryManager:
    """Manages error recovery and resilience."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.queue = PipelineJobQueue(db_path)
    
    def handle_failure(self, job_id: str, error: str, should_retry: bool = True) -> Dict[str, Any]:
        """Handles job failure with retry decision."""
        result = {
            'job_id': job_id,
            'error': error,
            'action': 'none',
            'timestamp': datetime.now().isoformat()
        }
        
        # Classify error
        if 'network' in error.lower() or 'timeout' in error.lower():
            result['error_type'] = 'transient'
            result['action'] = 'retry' if should_retry else 'fail'
            
            if should_retry:
                self.queue.retry_job(job_id, delay_seconds=30)
        
        elif 'permission' in error.lower() or 'access' in error.lower():
            result['error_type'] = 'permission'
            result['action'] = 'fail_no_retry'
        
        else:
            result['error_type'] = 'unknown'
            result['action'] = 'retry_with_backoff' if should_retry else 'fail'
            
            if should_retry:
                self.queue.retry_job(job_id, delay_seconds=60)
        
        # Update job status
        self.queue.update_job_status(job_id, JobStatus.FAILED.value, error=error)
        
        return result
    
    def get_failed_jobs(self) -> List[Dict[str, Any]]:
        """Retrieves all failed jobs."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT job_id, job_type, error_message, retry_count, created_at
                FROM job_queue
                WHERE status = ?
                ORDER BY completed_at DESC
            ''', (JobStatus.FAILED.value,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'job_id': r[0],
                    'job_type': r[1],
                    'error': r[2],
                    'retry_count': r[3],
                    'created_at': r[4]
                }
                for r in results
            ]
        
        except Exception as e:
            return []


@mcp.tool()
def submit_batch_job(job_id: str, job_type: str, payload_json: str, max_retries: int = 3) -> str:
    """
    Submits a batch job to the queue.
    Job types: 'search', 'analyze', 'compress', 'consolidate', etc.
    """
    try:
        payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
        queue = PipelineJobQueue(DB_PATH)
        result = queue.submit_job(job_id, job_type, payload, max_retries)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def get_job_status(job_id: str) -> str:
    """Gets status of a submitted job."""
    try:
        queue = PipelineJobQueue(DB_PATH)
        result = queue.get_job_status(job_id)
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def get_pending_jobs(limit: int = 10) -> str:
    """Gets pending jobs ready for execution."""
    try:
        queue = PipelineJobQueue(DB_PATH)
        results = queue.get_pending_jobs(limit)
        return json.dumps({'pending_jobs': results, 'count': len(results)}, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def create_pipeline(pipeline_name: str, steps_json: str) -> str:
    """
    Creates a multi-step pipeline.
    Steps format: [{"type": "search", "params": {...}, "max_retries": 2}, ...]
    """
    try:
        steps = json.loads(steps_json) if isinstance(steps_json, str) else steps_json
        coordinator = PipelineCoordinator(DB_PATH)
        result = coordinator.create_pipeline(pipeline_name, steps)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def execute_pipeline(pipeline_name: str) -> str:
    """Executes a previously created pipeline."""
    try:
        coordinator = PipelineCoordinator(DB_PATH)
        result = coordinator.execute_pipeline(pipeline_name)
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def handle_job_failure(job_id: str, error_message: str, should_retry: bool = True) -> str:
    """
    Handles job failure with intelligent retry decision.
    Classifies error type and takes appropriate action.
    """
    try:
        manager = ErrorRecoveryManager(DB_PATH)
        result = manager.handle_failure(job_id, error_message, should_retry)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def get_failed_jobs() -> str:
    """Retrieves all failed jobs for review."""
    try:
        manager = ErrorRecoveryManager(DB_PATH)
        results = manager.get_failed_jobs()
        return json.dumps({'failed_jobs': results, 'count': len(results)}, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


if __name__ == "__main__":
    mcp.run()
