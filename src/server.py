"""Main MCP server implementation using FastMCP"""

import sys
import logging
from fastmcp import FastMCP

from .config import Config
from .utils.client import FalClient
from .services import models, files, queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """Create and configure the MCP server"""
    # Load configuration
    logger.debug("Loading configuration from environment...")
    try:
        config = Config.from_env()
        logger.debug("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {type(e).__name__}: {str(e)}")
        raise
    
    # Initialize FastMCP server
    mcp = FastMCP(
        name="PMIND MCP fal.ai Server",
        instructions="""
This MCP server provides universal access to all fal.ai models without hardcoding specific model support.
It dynamically discovers model capabilities through OpenAPI schemas and provides comprehensive tools for:

Available tools:

Model Discovery:
- list_models: List all available models with pagination
- search_models: Search for models by keywords
- get_model_schema: Get OpenAPI schema for any model


Model Execution and File Management:
- run_model: Universal tool for running any fal.ai model (default mode: submit, also supports subscribe and run)
- upload_file: Upload local files to fal.ai
- upload_from_url: Download and upload files from URLs

Queue Management:
- check_queue_status: Check async job status
- get_queue_result: Get completed job results
- cancel_queue_request: Cancel queued or running jobs
- list_queue_requests: List all active requests in current session

Key Features:
- Works with any current or future fal.ai model
- Automatic parameter validation (only checks required parameters)
- Comprehensive error handling
- Support for all execution modes (run, subscribe, submit)
- File upload capabilities
- Async job tracking and management
- Schema caching for improved performance

Configuration:
- FAL_API_KEY: Required API key for authentication
- FAL_CACHE_DIR: Directory for caching model schemas

Authentication:
- Requires a valid fal.ai API key
- Get your key from https://fal.ai/dashboard/keys
"""
    )
    
    # Create shared client instance
    logger.debug("Creating shared fal.ai client...")
    client = FalClient(config)
    
    # Store config and client in server state for tools to access
    mcp.state = {"config": config, "client": client}
    
    # Register all tools
    models.register_tools(mcp, config, client)
    files.register_tools(mcp, config, client)
    queue.register_tools(mcp, config, client)
    
    logger.info("fal.ai MCP Server initialized successfully")
    
    return mcp


def main():
    """Main entry point"""
    try:
        mcp = create_server()
        mcp.run()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()