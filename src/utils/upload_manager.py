"""Upload manager for handling background file uploads to fal.ai"""

import json
import os
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import psutil
except ImportError:
    psutil = None

from ..config import Config


class UploadManager:
    """Manages background upload processes and state tracking."""
    
    def __init__(self, config: Config):
        self.config = config
        self.state_dir = Path(config.upload_state_dir).expanduser()
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def start_upload(self, file_path: str, upload_type: str = "file") -> Dict[str, Any]:
        """Start a background upload process."""
        # Validate file exists and size
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        if file_size > 10_485_760:  # 10MB limit
            raise ValueError(f"File too large: {file_size:,} bytes (max 10MB)")
        
        # Generate session ID
        session_id = f"upload_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        # Initialize state
        state = {
            "session_id": session_id,
            "file_path": str(file_path.absolute()),
            "file_size": file_size,
            "upload_type": upload_type,
            "status": "starting",
            "progress": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "error": None,
            "result_url": None,
            "pid": None,
            "retry_count": 0
        }
        
        self._save_state(session_id, state)
        
        # Start background worker process
        try:
            worker_script = Path(__file__).parent / "upload_worker.py"
            cmd = [
                sys.executable,
                str(worker_script),
                "--session-id", session_id,
                "--file-path", str(file_path),
                "--upload-type", upload_type,
                "--state-dir", str(self.state_dir),
                "--fal-api-key", self.config.fal_api_key
            ]
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from parent process group
            )
            
            # Update state with PID
            state["pid"] = proc.pid
            state["status"] = "uploading"
            self._save_state(session_id, state)
            
            return {
                "session_id": session_id,
                "status": "started",
                "file_size": file_size,
                "estimated_duration": self._estimate_upload_time(file_size)
            }
            
        except Exception as e:
            state["status"] = "failed"
            state["error"] = f"Failed to start upload process: {str(e)}"
            self._save_state(session_id, state)
            raise
    
    def get_upload_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of an upload."""
        state = self._load_state(session_id)
        if not state:
            raise ValueError(f"Upload session not found: {session_id}")
        
        # Check if process is still running
        if state.get("pid") and state["status"] in ["starting", "uploading"]:
            if not self._is_process_running(state["pid"]):
                # Process died, check for error in state
                state = self._load_state(session_id)  # Reload in case worker updated it
                if state["status"] not in ["completed", "failed", "cancelled"]:
                    state["status"] = "failed"
                    state["error"] = "Upload process died unexpectedly"
                    self._save_state(session_id, state)
        
        return {
            "session_id": session_id,
            "status": state["status"],
            "progress": state["progress"],
            "file_size": state["file_size"],
            "error": state.get("error"),
            "result_url": state.get("result_url"),
            "created_at": state["created_at"],
            "updated_at": state["updated_at"],
            "retry_count": state.get("retry_count", 0)
        }
    
    def get_upload_result(self, session_id: str) -> Dict[str, Any]:
        """Get the result of a completed upload."""
        status = self.get_upload_status(session_id)
        
        if status["status"] == "completed":
            return {
                "session_id": session_id,
                "url": status["result_url"],
                "file_size": status["file_size"]
            }
        elif status["status"] == "failed":
            raise Exception(f"Upload failed: {status['error']}")
        elif status["status"] == "cancelled":
            raise Exception("Upload was cancelled")
        else:
            raise Exception(f"Upload not completed yet. Status: {status['status']}")
    
    def cancel_upload(self, session_id: str) -> Dict[str, Any]:
        """Cancel an active upload."""
        state = self._load_state(session_id)
        if not state:
            raise ValueError(f"Upload session not found: {session_id}")
        
        if state["status"] in ["completed", "failed", "cancelled"]:
            return {"session_id": session_id, "status": "already_finished"}
        
        # Try to terminate the process
        if state.get("pid"):
            try:
                self._terminate_process(state["pid"])
            except (OSError, ProcessLookupError):
                pass  # Process might already be dead
        
        # Update state
        state["status"] = "cancelled"
        state["error"] = "Upload cancelled by user"
        state["updated_at"] = datetime.utcnow().isoformat()
        self._save_state(session_id, state)
        
        return {"session_id": session_id, "status": "cancelled"}
    
    def list_uploads(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all upload sessions."""
        uploads = []
        
        for state_file in self.state_dir.glob("upload_*.json"):
            try:
                state = self._load_state_from_file(state_file)
                if active_only and state["status"] not in ["starting", "uploading"]:
                    continue
                
                uploads.append({
                    "session_id": state["session_id"],
                    "status": state["status"],
                    "progress": state["progress"],
                    "file_size": state["file_size"],
                    "created_at": state["created_at"],
                    "updated_at": state["updated_at"]
                })
            except (json.JSONDecodeError, KeyError, OSError):
                continue  # Skip corrupted state files
        
        return sorted(uploads, key=lambda x: x["created_at"], reverse=True)
    
    def cleanup_old_uploads(self, max_age_hours: int = 24) -> int:
        """Clean up old upload state files."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned = 0
        
        for state_file in self.state_dir.glob("upload_*.json"):
            try:
                state = self._load_state_from_file(state_file)
                created_at = datetime.fromisoformat(state["created_at"])
                
                if created_at < cutoff and state["status"] in ["completed", "failed", "cancelled"]:
                    state_file.unlink()
                    cleaned += 1
            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                # Remove corrupted files
                state_file.unlink(missing_ok=True)
                cleaned += 1
        
        return cleaned
    
    def _save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """Save upload state to disk."""
        state_file = self.state_dir / f"{session_id}.json"
        state["updated_at"] = datetime.utcnow().isoformat()
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load upload state from disk."""
        state_file = self.state_dir / f"{session_id}.json"
        return self._load_state_from_file(state_file)
    
    def _load_state_from_file(self, state_file: Path) -> Optional[Dict[str, Any]]:
        """Load upload state from a file."""
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is still running."""
        try:
            os.kill(pid, 0)  # Check if process exists
            if psutil:
                try:
                    proc = psutil.Process(pid)
                    cmdline = ' '.join(proc.cmdline())
                    return 'upload_worker.py' in cmdline
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return True
            return True
        except OSError:
            return False
    
    def _terminate_process(self, pid: int) -> None:
        """Terminate a process gracefully."""
        try:
            # Try SIGTERM first
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            
            # Check if it's still running
            if self._is_process_running(pid):
                # Force kill
                os.kill(pid, signal.SIGKILL)
        except OSError:
            pass  # Process might already be dead
    
    def _estimate_upload_time(self, file_size: int) -> int:
        """Estimate upload time in seconds based on file size."""
        # Rough estimate: 1MB per 2 seconds
        return max(10, file_size // 524288)  # Minimum 10 seconds