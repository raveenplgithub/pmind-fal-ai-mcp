"""Model inference and schema services."""

import json

from pathlib import Path
from typing import Dict, Any, Optional, Annotated
from fastmcp import FastMCP
from pydantic import Field

from ..config import Config
from ..utils.client import FalClient
from ..utils.errors import ToolError
from ..utils.validators import sanitize_cache_filename
from ..utils.common import parse_bool_param, parse_int_param, parse_float_param


def register_tools(mcp: FastMCP, config: Config, client: FalClient):
    """Register model-related tools with the MCP server"""
    
    # Initialize schema cache and cache directory
    schema_cache = {}
    cache_dir = Path(config.fal_cache_dir).expanduser()
    cache_dir.mkdir(exist_ok=True)
    
    def get_cache_file_path(model_id: str) -> Path:
        """Get the cache file path for a model schema."""
        safe_filename = sanitize_cache_filename(model_id)
        return cache_dir / f"{safe_filename}.json"
    
    def load_schema_from_disk(cache_file: Path) -> Optional[Dict[str, Any]]:
        """Load schema from disk cache."""
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    def save_schema_to_disk(cache_file: Path, schema_data: Dict[str, Any]) -> None:
        """Save schema to disk cache."""
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, 'w') as f:
            json.dump(schema_data, f, indent=2)
    
    def extract_input_schema(openapi_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract the input schema from OpenAPI spec."""
        paths = openapi_schema.get("paths", {})
        
        # Find the main POST endpoint
        for _, methods in paths.items():
            if "post" in methods:
                post_endpoint = methods["post"]
                request_body = post_endpoint.get("requestBody", {})
                content = request_body.get("content", {})
                
                # Look for JSON content
                for content_type, content_data in content.items():
                    if "json" in content_type:
                        schema = content_data.get("schema", {})
                        
                        # Handle direct schema or $ref
                        if "$ref" in schema:
                            # Resolve reference
                            ref_path = schema["$ref"].split("/")
                            if ref_path[0] == "#" and ref_path[1] == "components" and ref_path[2] == "schemas":
                                schema_name = ref_path[3]
                                components = openapi_schema.get("components", {})
                                schemas = components.get("schemas", {})
                                return schemas.get(schema_name, {})
                        else:
                            return schema
        
        raise ToolError(
            "Could not extract input schema from OpenAPI specification. "
            "The model may not have a properly defined POST endpoint."
        )
    
    async def fetch_and_cache_schema(model_id: str) -> Dict[str, Any]:
        """Get the OpenAPI schema for a model."""
        
        # Check memory cache first
        if model_id in schema_cache:
            return schema_cache[model_id]
            
        # Check disk cache if available
        cache_file = get_cache_file_path(model_id)
        if cache_file.exists():
            schema_data = load_schema_from_disk(cache_file)
            if schema_data:
                schema_cache[model_id] = schema_data
                return schema_data
        
        # Fetch from API if not cached
        schema_data = await client.fetch_openapi_schema(model_id)
        
        # Save to disk cache
        save_schema_to_disk(cache_file, schema_data)
        
        # Cache in memory
        schema_cache[model_id] = schema_data
        
        return schema_data
    
    async def validate_model_parameters(model_id: str, parameters: Dict[str, Any]) -> None:
        """Validate parameters for a model before execution."""
        # Get schema
        schema_data = await fetch_and_cache_schema(model_id)
        
        # Extract input schema from OpenAPI
        input_schema = extract_input_schema(schema_data)
        
        # Check required parameters
        required = input_schema.get("required", [])
        missing = [param for param in required if param not in parameters]
        
        if missing:
            missing_params = ", ".join(missing)
            raise ToolError(
                f"Missing required parameters for {model_id}: {missing_params}. "
                f"Required parameters: {', '.join(required)}"
            )
    
    @mcp.tool
    async def run_model(
        model_id: Annotated[str, Field(
            description="Model identifier (e.g., 'fal-ai/flux/dev', 'fal-ai/veo3')"
        )],
        parameters: Annotated[Dict[str, Any], Field(
            description="Model-specific parameters. Use get_model_schema to see required parameters."
        )],
        mode: Annotated[str, Field(
            default="submit",
            description="Execution mode: 'submit' (async, returns request_id), 'subscribe' (submit and wait), 'run' (blocking)"
        )] = "submit",
        webhook_url: Annotated[Optional[str], Field(
            default=None,
            description="Optional webhook URL for async notifications (only for 'submit' mode)"
        )] = None,
        priority: Annotated[Optional[int], Field(
            default=None,
            description="Optional priority level for queue (only for 'submit' mode)"
        )] = None,
        path: Annotated[str, Field(
            default='',
            description="Optional path parameter for the model endpoint"
        )] = '',
        timeout: Annotated[Optional[float], Field(
            default=None,
            description="Optional timeout in seconds for the request"
        )] = None,
        hint: Annotated[Optional[str], Field(
            default=None,
            description="Optional hint for model execution"
        )] = None,
        with_logs: Annotated[bool, Field(
            default=False,
            description="Whether to include logs (only for 'subscribe' mode)"
        )] = False
    ) -> Dict[str, Any]:
        """Run any fal.ai model with automatic parameter validation. This is the universal tool for model inference."""
        
        # Always validate parameters
        await validate_model_parameters(model_id, parameters)
        
        # Parse parameters that might come as strings
        priority = parse_int_param(priority)
        timeout = parse_float_param(timeout)
        with_logs = parse_bool_param(with_logs) if with_logs is not None else False
        
        # Execute based on mode
        if mode == "run":
            return await client.run(model_id, parameters, path=path, timeout=timeout, hint=hint)
        elif mode == "submit":
            return await client.submit(model_id, parameters, webhook_url, priority, path=path, hint=hint)
        else:  # subscribe
            return await client.subscribe(
                model_id, parameters, 
                path=path, hint=hint, with_logs=with_logs, priority=priority
            )
    
    @mcp.tool
    async def list_models(
        page: Annotated[Optional[int], Field(
            default=None,
            description="Page number for pagination"
        )] = None,
        total: Annotated[Optional[int], Field(
            default=None,
            description="Total number of models per page"
        )] = None
    ) -> Dict[str, Any]:
        """List available models on fal.ai with pagination. Note: This uses an undocumented API endpoint."""
        # Parse parameters that might come as strings
        page = parse_int_param(page)
        total = parse_int_param(total)
        
        return await client.list_models(page, total)
    
    @mcp.tool
    async def search_models(
        keywords: Annotated[str, Field(
            description="Search terms to find models"
        )]
    ) -> Dict[str, Any]:
        """Search for models on fal.ai based on keywords. Note: This uses an undocumented API endpoint."""
        return await client.search_models(keywords)
    
    @mcp.tool
    async def get_model_schema(
        model_id: Annotated[str, Field(
            description="Model identifier (e.g., 'fal-ai/flux/dev', 'fal-ai/veo3')"
        )]
    ) -> Dict[str, Any]:
        """Get the OpenAPI schema for any fal.ai model. Use this to understand what parameters a model accepts. Note: This uses an undocumented API endpoint."""
        return await fetch_and_cache_schema(model_id)
    
