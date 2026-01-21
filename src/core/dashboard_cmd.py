"""
Control Room Orchestrator - Launches API and Frontend
"""

import subprocess
import os
import sys
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DashboardOrchestrator:
    """Manages the lifecycle of the Control Room components."""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.api_process = None
        self.frontend_process = None

    def start(self):
        """Start both backend and frontend."""
        print("\n🚀 Launching SimpleMem Control Room...")
        
        try:
            # 1. Start FastAPI Backend
            print("   -> Starting Backend API (Port 8000)...")
            api_cmd = [
                sys.executable, "-m", "uvicorn", 
                "src.api.main:app", 
                "--host", "127.0.0.1", 
                "--port", "8000"
            ]
            self.api_process = subprocess.Popen(
                api_cmd, 
                cwd=self.root_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            # 2. Start Frontend Dev Server
            print("   -> Starting Frontend Dashboard (Vite)...")
            frontend_dir = self.root_dir / "frontend"
            if not frontend_dir.exists():
                print("   ❌ Error: Frontend directory not found. Did you run initialization?")
                self.api_process.terminate()
                return

            frontend_cmd = ["npm", "run", "dev"]
            # Use shell=True for npm on Windows
            self.frontend_process = subprocess.Popen(
                frontend_cmd, 
                cwd=frontend_dir,
                shell=True
            )
            
            print("\n✅ Control Room is initializing!")
            print("   - API:      http://127.0.0.1:8000")
            print("   - Dashboard: http://localhost:5173 (usually)")
            print("\nPress Ctrl+C in this terminal to shut down all components.\n")
            
            # Keep alive and monitor
            while True:
                if self.api_process.poll() is not None:
                    print("❌ Backend process terminated unexpectedly.")
                    break
                if self.frontend_process.poll() is not None:
                    print("❌ Frontend process terminated unexpectedly.")
                    break
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Control Room components...")
            self.stop()
        except Exception as e:
            print(f"❌ Error: {e}")
            self.stop()

    def stop(self):
        """Gracefully stop all processes."""
        if self.api_process:
            self.api_process.terminate()
        if self.frontend_process:
            # On Windows, terminating a shell process needs care
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.frontend_process.pid)], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("Control Room shutdown complete")

def main(args=None):
    orchestrator = DashboardOrchestrator()
    orchestrator.start()

if __name__ == "__main__":
    main()
