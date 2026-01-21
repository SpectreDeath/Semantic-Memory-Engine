"""
Batch Processor - Asynchronous batch processing for SimpleMem.

Features:
- Async job submission
- Status tracking
- Result aggregation
- Error handling at item level
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class BatchJob:
    """Represents a batch processing job."""
    
    def __init__(self, job_id: str, items: List[Any], processor: Callable):
        self.job_id = job_id
        self.items = items
        self.processor = processor
        self.status = "pending"
        self.results = []
        self.errors = []
        self.created_at = datetime.now()
        self.completed_at = Optional[datetime]
        self.progress = 0.0

class BatchProcessor:
    """Manager for asynchronous batch jobs."""
    
    def __init__(self):
        self.jobs: Dict[str, BatchJob] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, items: List[Any], processor: Callable) -> str:
        """Create a new batch job."""
        job_id = str(uuid.uuid4())
        job = BatchJob(job_id, items, processor)
        async with self._lock:
            self.jobs[job_id] = job
        
        # Start processing in background
        asyncio.create_task(self._process_job(job_id))
        return job_id

    async def _process_job(self, job_id: str):
        """Process job items asynchronously."""
        job = self.jobs.get(job_id)
        if not job:
            return

        job.status = "processing"
        total = len(job.items)
        
        for i, item in enumerate(job.items):
            try:
                # In a real app, this might be calling NLP tools
                result = await job.processor(item)
                job.results.append(result)
            except Exception as e:
                logger.error(f"Error processing item in job {job_id}: {e}")
                job.errors.append({"item_index": i, "error": str(e)})
            
            job.progress = (i + 1) / total

        job.status = "completed"
        job.completed_at = datetime.now()
        logger.info(f"Batch job {job_id} completed with {len(job.results)} successes and {len(job.errors)} errors")

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status and progress of a job."""
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "item_count": len(job.items),
            "success_count": len(job.results),
            "error_count": len(job.errors),
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }

    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the results of a completed job."""
        job = self.jobs.get(job_id)
        if not job or job.status != "completed":
            return None
        
        return {
            "results": job.results,
            "errors": job.errors
        }

# Global processor instance
_processor = BatchProcessor()

def get_batch_processor() -> BatchProcessor:
    return _processor
