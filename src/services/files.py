"""File management services."""

from typing import Dict, Any, Optional, Annotated
from fastmcp import FastMCP
from pydantic import Field

from ..config import Config
from ..utils.client import FalClient
from ..utils.validators import validate_file_path
from ..utils.upload_manager import UploadManager


def register_tools(mcp: FastMCP, config: Config, client: FalClient):
    """Register file-related tools with the MCP server"""
    
    # Initialize upload manager
    upload_manager = UploadManager(config)
    
    @mcp.tool
    async def upload_file(
        file_path: Annotated[str, Field(
            description="Path to the file to upload"
        )]
    ) -> Dict[str, Any]:
        """Upload a file to fal.ai storage. Returns immediately with a session ID for tracking progress."""
        # Validate file path
        path = validate_file_path(file_path)
        return upload_manager.start_upload(str(path), "file")
    
    @mcp.tool
    async def upload_from_url(
        url: Annotated[str, Field(
            description="URL of the file to download and upload"
        )]
    ) -> Dict[str, Any]:
        """Upload a file from URL to fal.ai storage. Returns immediately with a session ID for tracking progress."""
        return upload_manager.start_upload(url, "url")
    
    @mcp.tool
    async def download_file(
        url: Annotated[str, Field(
            description="URL of the file to download (e.g., generated image or file)"
        )],
        filename: Annotated[Optional[str], Field(
            default=None,
            description="Optional filename to save as (will auto-detect from URL if not provided)"
        )] = None,
        download_dir: Annotated[Optional[str], Field(
            default=None,
            description="Directory to download to (defaults to current directory if not provided)"
        )] = None
    ) -> Dict[str, Any]:
        """Download a file from a URL to local filesystem."""
        return await client.download_file(url, filename, download_dir)
    
    @mcp.tool
    async def check_upload_status(
        session_id: Annotated[str, Field(
            description="Upload session ID returned from upload_file or upload_from_url"
        )]
    ) -> Dict[str, Any]:
        """Check the status of an upload operation. Returns progress, status, and error information."""
        return upload_manager.get_upload_status(session_id)
    
    @mcp.tool
    async def get_upload_result(
        session_id: Annotated[str, Field(
            description="Upload session ID for a completed upload"
        )]
    ) -> Dict[str, Any]:
        """Get the result URL from a completed upload. Only works after upload status is 'completed'."""
        return upload_manager.get_upload_result(session_id)
    
    @mcp.tool
    async def cancel_upload(
        session_id: Annotated[str, Field(
            description="Upload session ID to cancel"
        )]
    ) -> Dict[str, Any]:
        """Cancel an active upload operation. The background process will be terminated."""
        return upload_manager.cancel_upload(session_id)
    
    @mcp.tool
    async def list_uploads(
        active_only: Annotated[bool, Field(
            default=False,
            description="If True, only show active uploads. If False, show all uploads."
        )] = False
    ) -> Dict[str, Any]:
        """List all upload sessions, optionally filtering to active ones only."""
        uploads = upload_manager.list_uploads(active_only)
        return {
            "uploads": uploads,
            "total_count": len(uploads),
            "active_only": active_only
        }
    
    @mcp.tool
    async def cleanup_old_uploads(
        max_age_hours: Annotated[int, Field(
            default=24,
            description="Maximum age in hours for upload state files to keep"
        )] = 24
    ) -> Dict[str, Any]:
        """Clean up old upload state files to free disk space."""
        cleaned_count = upload_manager.cleanup_old_uploads(max_age_hours)
        return {
            "cleaned_count": cleaned_count,
            "max_age_hours": max_age_hours
        }