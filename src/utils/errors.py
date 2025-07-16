"""Error handling utilities for fal.ai MCP server."""


class ToolError(Exception):
    """Error to be shown to the MCP client with a user-friendly message."""
    pass