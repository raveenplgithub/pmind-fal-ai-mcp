"""Queue management services for async operations."""

from datetime import datetime
from typing import Dict, Any, Annotated
from fastmcp import FastMCP
from pydantic import Field

from ..config import Config
from ..utils.client import FalClient
from ..utils.common import parse_bool_param


def register_tools(mcp: FastMCP, config: Config, client: FalClient):
    """Register queue-related tools with the MCP server"""
    
    # Track active requests
    active_requests = {}
    
    @mcp.tool
    async def check_queue_status(
        model_id: Annotated[str, Field(
            description="Model identifier used for the request"
        )],
        request_id: Annotated[str, Field(
            description="Request ID returned from run_model with mode='submit'"
        )],
        with_logs: Annotated[bool, Field(
            default=False,
            description="Whether to include execution logs"
        )] = False
    ) -> Dict[str, Any]:
        """Check the status of an async job submitted to fal.ai."""

        
        # Parse parameters that might come as strings
        with_logs = parse_bool_param(with_logs) if with_logs is not None else False
        
        result = await client.status(model_id, request_id, with_logs=with_logs)

        # Update tracked status
        if request_id in active_requests and result.get("status"):
            active_requests[request_id]["status"] = result["status"]
            active_requests[request_id]["last_checked"] = datetime.now().isoformat()
        return result
    
    @mcp.tool
    async def get_queue_result(
        model_id: Annotated[str, Field(
            description="Model identifier used for the request"
        )],
        request_id: Annotated[str, Field(
            description="Request ID of the completed job"
        )]
    ) -> Dict[str, Any]:
        """Get the result of a completed async job."""

        result = await client.result(model_id, request_id)

        # Remove from active tracking
        if request_id in active_requests:
            active_requests.pop(request_id)
        
        return result
    
    @mcp.tool
    async def cancel_queue_request(
        model_id: Annotated[str, Field(
            description="Model identifier used for the request"
        )],
        request_id: Annotated[str, Field(
            description="Request ID to cancel"
        )]
    ) -> Dict[str, Any]:
        """Cancel a queued or running async job."""

        result = await client.cancel(model_id, request_id)

        # Update tracking
        if request_id in active_requests:
            active_requests[request_id]["status"] = "cancelled"
            active_requests[request_id]["cancelled_at"] = datetime.now().isoformat()
        
        return result
    
    @mcp.tool
    async def list_queue_requests() -> Dict[str, Any]:
        """List all active async requests tracked in this session."""
        
        # Format active requests
        requests = []
        for request_id, info in active_requests.items():
            requests.append({
                "request_id": request_id,
                "model_id": info["model_id"],
                "status": info.get("status", "unknown"),
                "submitted_at": info["submitted_at"],
                "last_checked": info.get("last_checked")
            })
        
        # Sort by submission time (newest first)
        requests.sort(key=lambda x: x["submitted_at"], reverse=True)
        
        return {
            "active_requests": requests,
            "count": len(requests)
        }