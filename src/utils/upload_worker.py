#!/usr/bin/env python3
"""Background worker for handling fal.ai file uploads."""

import argparse
import json
import os
import signal
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import fal_client
import httpx


class UploadWorker:
    """Background worker that handles actual file uploads to fal.ai."""
    
    def __init__(self, session_id: str, file_path: str, upload_type: str, 
                 state_dir: str, fal_api_key: str):
        self.session_id = session_id
        self.file_path = Path(file_path)
        self.upload_type = upload_type
        self.state_dir = Path(state_dir)
        self.fal_api_key = fal_api_key
        self.interrupted = False
        
        # Set up fal.ai API key
        os.environ["FAL_KEY"] = fal_api_key
        
        # Set up signal handlers for graceful termination
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def run(self) -> None:
        """Main worker execution."""
        try:
            self._update_state({"status": "uploading", "progress": 0.0})
            
            if self.upload_type == "file":
                result_url = self._upload_file()
            elif self.upload_type == "url":
                result_url = self._upload_from_url()
            else:
                raise ValueError(f"Unknown upload type: {self.upload_type}")
            
            if self.interrupted:
                self._update_state({"status": "cancelled", "error": "Upload interrupted"})
                return
            
            self._update_state({
                "status": "completed",
                "progress": 1.0,
                "result_url": result_url
            })
            
        except Exception as e:
            self._handle_error(e)
    
    def _upload_file(self) -> str:
        """Upload a local file to fal.ai."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        # Update progress
        self._update_state({"progress": 0.1, "status": "uploading"})
        
        # Perform the upload with retry logic
        for attempt in range(3):
            if self.interrupted:
                raise InterruptedError("Upload interrupted")
            
            try:
                # Use synchronous upload_file (it's actually quite fast)
                result_url = fal_client.upload_file(str(self.file_path))
                
                self._update_state({"progress": 0.9})
                return result_url
                
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise
                
                # Exponential backoff
                wait_time = 2 ** attempt
                self._update_state({
                    "error": f"Upload attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...",
                    "retry_count": attempt + 1
                })
                time.sleep(wait_time)
    
    def _upload_from_url(self) -> str:
        """Upload from URL to fal.ai (file_path contains the URL)."""
        url = str(self.file_path)
        
        self._update_state({"progress": 0.1, "status": "downloading"})
        
        # Download the file first
        temp_file = None
        try:
            with httpx.Client() as client:
                response = client.get(url)
                response.raise_for_status()
                
                # Determine file extension
                url_path = url.split('?')[0]
                suffix = Path(url_path).suffix or '.tmp'
                
                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                temp_file.write(response.content)
                temp_file.close()
                
                self._update_state({"progress": 0.5, "status": "uploading"})
                
                # Upload the temp file
                result_url = fal_client.upload_file(temp_file.name)
                
                self._update_state({"progress": 0.9})
                return result_url
                
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def _update_state(self, updates: Dict[str, Any]) -> None:
        """Update the upload state file."""
        state_file = self.state_dir / f"{self.session_id}.json"
        
        # Load current state
        state = {}
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        
        # Update with new values
        state.update(updates)
        state["updated_at"] = datetime.utcnow().isoformat()
        
        # Save back to file
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            # If we can't save state, at least print to stderr
            print(f"Failed to save state: {e}", file=sys.stderr)
    
    def _handle_error(self, error: Exception) -> None:
        """Handle upload errors with proper logging."""
        error_msg = str(error)
        
        # Classify error types
        if "timeout" in error_msg.lower() or "504" in error_msg:
            error_type = "timeout"
        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            error_type = "network"
        elif "file" in error_msg.lower() and "not found" in error_msg.lower():
            error_type = "file_not_found"
        elif "too large" in error_msg.lower() or "size" in error_msg.lower():
            error_type = "file_too_large"
        else:
            error_type = "unknown"
        
        self._update_state({
            "status": "failed",
            "error": error_msg,
            "error_type": error_type
        })
        
        # Print to stderr for debugging
        print(f"Upload failed [{error_type}]: {error_msg}", file=sys.stderr)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle termination signals."""
        self.interrupted = True
        self._update_state({"status": "cancelled", "error": "Upload interrupted by signal"})
        sys.exit(0)


def main():
    """Main entry point for the upload worker."""
    parser = argparse.ArgumentParser(description="Background upload worker for fal.ai")
    parser.add_argument("--session-id", required=True, help="Upload session ID")
    parser.add_argument("--file-path", required=True, help="Path to file or URL to upload")
    parser.add_argument("--upload-type", required=True, choices=["file", "url"], 
                       help="Type of upload")
    parser.add_argument("--state-dir", required=True, help="Directory for state files")
    parser.add_argument("--fal-api-key", required=True, help="fal.ai API key")
    
    args = parser.parse_args()
    
    worker = UploadWorker(
        session_id=args.session_id,
        file_path=args.file_path,
        upload_type=args.upload_type,
        state_dir=args.state_dir,
        fal_api_key=args.fal_api_key
    )
    
    worker.run()


if __name__ == "__main__":
    main()