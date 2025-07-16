"""fal.ai client wrapper with enhanced error handling and features."""
import os
import tempfile
import fal_client
import httpx

from typing import Any, Dict, Optional, Union
from pathlib import Path

from ..config import Config

class FalClient:
    """Enhanced fal.ai client wrapper."""
    
    def __init__(self, config: Config):
        self.config = config
        # fal_client reads API key from FAL_KEY environment variable
        os.environ["FAL_KEY"] = self.config.fal_api_key
    
    async def run(self, model_id: str, arguments: Dict[str, Any], 
                  path: str = '', timeout: Optional[float] = None, 
                  hint: Optional[str] = None) -> Any:
        """Run a model and wait for the result."""
        return await fal_client.run_async(
            model_id,
            arguments,
            path=path,
            timeout=timeout,
            hint=hint
        )
    
    async def subscribe(self, model_id: str, arguments: Dict[str, Any],
                       path: str = '', hint: Optional[str] = None,
                       with_logs: bool = False, on_enqueue: Optional[Any] = None,
                       on_queue_update: Optional[Any] = None, 
                       priority: Optional[int] = None) -> Any:
        """Subscribe to a model (submit and wait for result)."""
        return await fal_client.subscribe_async(
            model_id,
            arguments,
            path=path,
            hint=hint,
            with_logs=with_logs,
            on_enqueue=on_enqueue,
            on_queue_update=on_queue_update,
            priority=priority
        )
    
    async def submit(self, model_id: str, arguments: Dict[str, Any],
                    webhook_url: Optional[str] = None, priority: Optional[int] = None,
                    path: str = '', hint: Optional[str] = None) -> Dict[str, Any]:
        """Submit an async request to a model."""
        # Build kwargs for optional parameters
        kwargs = {}
        if webhook_url:
            kwargs["webhook_url"] = webhook_url
        if priority is not None:
            kwargs["priority"] = priority
        
        handle = await fal_client.submit_async(
            model_id,
            arguments,
            path=path,
            hint=hint,
            **kwargs
        )
    
        return {
            "request_id": handle.request_id,
            "response_url": handle.response_url,
            "status_url": handle.status_url,
            "cancel_url": handle.cancel_url
        }

    async def status(self, model_id: str, request_id: str, 
                    with_logs: bool = False) -> Dict[str, Any]:
        """Check the status of an async request."""
        status = await fal_client.status_async(
            model_id,
            request_id,
            with_logs=with_logs
        )
        
        # Simple approach: just extract the status type and logs
        result = {
            "status": status.__class__.__name__.lower(),
            "request_id": request_id
        }
        
        # Add logs if available
        if hasattr(status, 'logs') and status.logs is not None:
            result["logs"] = status.logs
            
        return result
    
    async def result(self, model_id: str, request_id: str) -> Any:
        """Get the result of a completed async request."""
        return await fal_client.result_async(
            model_id,
            request_id
        )
    
    async def cancel(self, model_id: str, request_id: str) -> Any:
        """Cancel an async request."""
        return await fal_client.cancel_async(
            model_id,
            request_id
        )
    
    async def upload_file(self, file_path: Union[str, Path]) -> str:
        """Upload a file to fal.ai storage."""
        file_path = Path(file_path)
        
        return fal_client.upload_file(
            str(file_path)
        )
    
    async def upload_from_url(self, url: str, filename: Optional[str] = None) -> str:
        """Download a file from URL and upload to fal.ai."""
        # Download file
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Determine file extension
            if filename:
                suffix = Path(filename).suffix
            else:
                # Try to extract from URL
                url_path = url.split('?')[0]  # Remove query params
                suffix = Path(url_path).suffix
            
            # Create temp file with proper extension
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
        
        try:
            # Upload to fal.ai
            return await self.upload_file(tmp_path)
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)
    
    async def fetch_openapi_schema(self, model_id: str) -> Dict[str, Any]:
        """Fetch OpenAPI schema for a model."""
        # Construct OpenAPI URL
        openapi_url = f"{self.config.api_url}/openapi/queue/openapi.json?endpoint_id={model_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(openapi_url)
            response.raise_for_status()
            return response.json()
    
    async def http_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a public (non-authenticated) request."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def list_models(self, page: Optional[int] = None, 
                         total: Optional[int] = None) -> Any:
        """List available models with pagination."""
        url = f"{self.config.api_url}/models"
        params = {}
        if page is not None:
            params["page"] = page
        if total is not None:
            params["total"] = total
        
        return await self.http_request(url, params)
    
    async def search_models(self, keywords: str) -> Any:
        """Search for models by keywords."""
        url = f"{self.config.api_url}/models"
        params = {"keywords": keywords}
        
        return await self.http_request(url, params)
    
    async def download_file(self, url: str, filename: Optional[str] = None, 
                           download_dir: Optional[str] = None) -> Dict[str, Any]:
        """Download a file from a URL to local filesystem."""
        download_path = Path(download_dir) if download_dir else Path(self.config.fal_download_dir).expanduser()
        download_path.mkdir(parents=True, exist_ok=True)
        
        # Determine filename
        if not filename:
            # Extract filename from URL
            url_path = url.split('?')[0]  # Remove query params
            filename = Path(url_path).name
            if not filename or '.' not in filename:
                filename = "downloaded_file"
        
        file_path = download_path / filename
        
        # Download the file
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Write to file
            with open(file_path, 'wb') as f:
                f.write(response.content)
        
        return {
            "filename": filename,
            "file_path": str(file_path.absolute()),
            "size_bytes": len(response.content),
            "download_dir": str(download_path.absolute()),
            "url": url
        }