"""Configuration handling for fal.ai MCP server"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class Config(BaseSettings):
    """Server configuration"""
    model_config = SettingsConfigDict(env_prefix='')
    
    fal_api_key: str = Field(..., description="fal.ai API key for authentication")
    fal_cache_dir: str = Field(..., description="Directory for caching model schemas")
    fal_download_dir: str = Field(default=".", description="Default directory for file downloads")
    fal_upload_state_dir: str = Field(..., description="Directory for upload state tracking")
    
    # API endpoint
    api_url: str = Field(default="https://fal.ai/api", description="API URL for public endpoints")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        # Load .env file if it exists
        load_dotenv()
        
        # Pydantic will automatically read from environment variables
        # and raise ValidationError if required fields are missing
        return cls()