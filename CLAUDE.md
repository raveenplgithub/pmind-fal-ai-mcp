# pmind-fal-ai-mcp

## Overview
This is an MCP (Model Context Protocol) server for fal.ai that provides universal access to all fal.ai models without hardcoding. It dynamically discovers model capabilities through OpenAPI schemas.

## Key Features
- Universal model support - no hardcoded models
- Dynamic schema discovery via OpenAPI
- Comprehensive error handling
- Schema caching for performance
- Support for sync/async/streaming execution
- Background upload system with progress tracking
- File download capabilities
- Queue management for async operations

## Architecture Patterns
This project follows the same patterns as pmind-youtube-mcp:
- `Config.from_env()` pattern for configuration
- `create_server()` function for server instantiation
- `register_tools()` pattern in each service module
- Service classes for organizing functionality
- Consistent error handling with `format_error_response()`
- Background process architecture for long-running operations

## Project Structure
```
src/
├── config.py           # Configuration with from_env() pattern
├── server.py           # Main server with create_server() function
├── services/           # Service modules with register_tools() pattern
│   ├── schema.py       # Model exploration and schema discovery
│   ├── models.py       # Model inference (run, submit, subscribe)
│   ├── files.py        # File upload/download management
│   └── queue.py        # Async job queue management
└── utils/              # Utilities
    ├── client.py       # fal.ai client wrapper
    ├── upload_manager.py  # Background upload orchestration
    ├── upload_worker.py   # Upload worker process
    ├── validators.py   # Dynamic schema validation
    ├── common.py       # Common utilities
    └── errors.py       # Error handling
```

## Development Commands
```bash
# Install dependencies
uv sync

# Run linting
uv run ruff check src/ --fix

# Run the server (requires FAL_API_KEY env var)
uv run pmind-fal-ai
```

## Environment Variables
- `FAL_API_KEY` - Required: Your fal.ai API key
- `FAL_CACHE_DIR` - Required: Directory for caching model schemas
- `FAL_DOWNLOAD_DIR` - Optional: Directory for file downloads (defaults to current directory)
- `UPLOAD_STATE_DIR` - Required: Directory for upload state tracking

## Background Upload System

The upload system follows the YouTube MCP pattern for handling long-running operations:

### Architecture
1. **Upload Manager** (`upload_manager.py`)
   - Spawns background processes
   - Tracks upload sessions
   - Manages process lifecycle
   - Handles cleanup

2. **Upload Worker** (`upload_worker.py`)
   - Runs in separate process
   - Executes actual uploads
   - Implements retry logic
   - Updates state files

### Key Features
- **No Timeouts**: Background processes avoid MCP timeout limits
- **Progress Tracking**: Real-time upload progress with persistent state
- **Session Management**: Upload sessions survive MCP server restarts
- **Automatic Retry**: Failed uploads retry with exponential backoff
- **Error Classification**: Different error types for better debugging

### Upload Flow
```
1. Client calls upload_file(path)
2. Upload Manager validates file and creates session
3. Background worker process spawned
4. Client receives session_id immediately
5. Worker uploads file with progress updates
6. Client polls status with check_upload_status(session_id)
7. Client gets URL with get_upload_result(session_id)
```

## Key Tools
1. **list_models** - List all models with pagination (inspired by mcp-fal)
2. **search_models** - Search models by keywords (inspired by mcp-fal)
3. **get_model_schema** - Get OpenAPI schema for any model
4. **run_model** - Universal model execution tool (supports run, submit, subscribe modes)
5. **upload_file** - Upload files with background processing
6. **upload_from_url** - Upload from URL with background processing
7. **check_upload_status** - Monitor upload progress
8. **get_upload_result** - Get completed upload URL
9. **cancel_upload** - Cancel active uploads
10. **list_uploads** - View all upload sessions
11. **cleanup_old_uploads** - Clean up old state files
12. **download_file** - Download files to local storage
13. **check_queue_status** - Check async job status
14. **get_queue_result** - Get completed job results
15. **cancel_queue_request** - Cancel queued or running jobs
16. **list_queue_requests** - List active queue requests

## Implementation Notes
- All models are accessed through their OpenAPI schemas
- No models are hardcoded - fully dynamic discovery
- Schema caching improves performance
- Comprehensive parameter validation before execution
- Support for all fal.ai execution modes (sync, async, stream)
- Upload state persisted to disk for reliability
- Process management with graceful termination

## Key Features
- **Model Discovery**: List and search models with pagination
- **Queue Management**: Queue position tracking
- **File Operations**: Background uploads with validation
- **Download Support**: Save generated files locally
- **Error Handling**: Native fal_client error handling with input validation
- **Progress Tracking**: Real-time upload progress updates

## fal_client Documentation
The official fal_client Python library documentation: https://fal-ai.github.io/fal/client/fal_client.html

Key async methods we use:
- `run_async(application, arguments, *, path='', timeout=None, hint=None)`
- `submit_async(application, arguments, *, path='', hint=None, webhook_url=None, priority=None)`
- `subscribe_async(application, arguments, *, path='', hint=None, with_logs=False, on_enqueue=None, on_queue_update=None, priority=None)`
- `status_async(application, request_id, *, with_logs=False)`
- `result_async(application, request_id)`
- `cancel_async(application, request_id)`
- `upload_file(path)` - Note: This is synchronous, wrapped in background process

## Important Constraints
- **10MB File Limit**: fal.ai rejects files larger than 10MB
- **No Chunked Uploads**: fal_client doesn't support chunked uploads yet
- **Synchronous upload_file**: We wrap it in background process for async behavior

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.