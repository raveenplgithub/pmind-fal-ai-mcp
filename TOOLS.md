# PMIND fal.ai MCP Tools Reference

Complete documentation of all available tools in the fal.ai MCP server.

## Model Discovery Tools

### 1. **list_models**
List all available models on fal.ai with pagination support.

**Parameters:**
- `page` (optional): Page number for pagination
- `total` (optional): Total number of models per page

**Example prompts:**
- "List all available models"
- "Show me page 2 of models with 20 per page"
- "What models are available on fal.ai?"

**Note:** This uses an undocumented API endpoint and may be subject to changes.

### 2. **search_models**
Search for models by keywords to find specific capabilities.

**Parameters:**
- `keywords` (required): Search terms to find models

**Example prompts:**
- "Search for image generation models"
- "Find models related to video"
- "Look for flux models"
- "Search for stable diffusion models"

**Note:** This uses an undocumented API endpoint and may be subject to changes.

### 3. **get_model_schema**
Get the complete OpenAPI schema for any fal.ai model to understand its parameters.

**Parameters:**
- `model_id` (required): Model identifier (e.g., 'fal-ai/flux/dev', 'fal-ai/veo3')

**Example prompts:**
- "Get the schema for fal-ai/flux/dev"
- "What parameters does fal-ai/veo3 accept?"
- "Show me the API documentation for stable-diffusion"

**Use cases:**
- Understanding required and optional parameters
- Checking parameter types and constraints
- Exploring model capabilities before use

## Model Execution Tools

### 4. **run_model**
Universal tool for running any fal.ai model with automatic parameter validation.

**Parameters:**
- `model_id` (required): Model identifier (e.g., 'fal-ai/flux/dev')
- `parameters` (required): Model-specific parameters (use get_model_schema to see requirements)
- `mode` (optional): Execution mode - 'submit' (async, default), 'subscribe' (submit and wait), 'run' (blocking)
- `webhook_url` (optional): URL for async notifications (only for 'submit' mode)
- `priority` (optional): Priority level for queue (only for 'submit' mode)
- `path` (optional): Path parameter for the model endpoint (default: '')
- `timeout` (optional): Timeout in seconds for the request
- `hint` (optional): Hint for model execution
- `with_logs` (optional): Include logs (only for 'subscribe' mode, default: false)

**Example prompts:**
- "Generate an image of a mountain landscape with FLUX"
- "Run fal-ai/veo3 to create a video of a dancing robot"
- "Submit an async job to generate art with stable diffusion"
- "Run image enhancement on my uploaded photo"

**Execution modes explained:**
- `submit`: Returns immediately with a request_id for tracking
- `subscribe`: Submits and waits for completion
- `run`: Blocks until completion (synchronous)

## File Management Tools

### 5. **upload_file**
Upload a local file to fal.ai storage. Returns immediately with a session ID for tracking progress.

**Parameters:**
- `file_path` (required): Path to the file to upload

**Example prompts:**
- "Upload the file at /home/user/image.jpg"
- "Upload my local video.mp4 for processing"
- "Upload the image from my desktop"

**Returns:**
- `session_id`: Unique ID to track upload progress
- `status`: Current status ('started')
- `file_size`: Size of the file in bytes
- `estimated_duration`: Estimated upload time in seconds

**Note:** Files must be under 10MB (fal.ai limit). Use `check_upload_status` to monitor progress.

### 6. **upload_from_url**
Upload a file from URL to fal.ai storage. Returns immediately with a session ID for tracking progress.

**Parameters:**
- `url` (required): URL of the file to download and upload

**Example prompts:**
- "Upload the image from https://example.com/photo.jpg"
- "Download and upload this video URL for processing"
- "Get this file from the web and prepare it for model input"

**Returns:**
- `session_id`: Unique ID to track upload progress
- `status`: Current status ('started')
- `file_size`: Size of the file in bytes
- `estimated_duration`: Estimated upload time in seconds

### 7. **check_upload_status**
Check the status of an upload operation. Returns progress, status, and error information.

**Parameters:**
- `session_id` (required): Upload session ID returned from upload_file or upload_from_url

**Example prompts:**
- "Check the status of upload session upload_abc123_1234567890"
- "How is my file upload progressing?"
- "Is my upload complete?"

**Returns:**
- `session_id`: The upload session ID
- `status`: Current status ('starting', 'uploading', 'completed', 'failed', 'cancelled')
- `progress`: Upload progress (0.0 to 1.0)
- `file_size`: Size of the file in bytes
- `error`: Error message if failed
- `result_url`: Final URL if completed
- `created_at`: When upload started
- `updated_at`: Last status update
- `retry_count`: Number of retry attempts

### 8. **get_upload_result**
Get the result URL from a completed upload. Only works after upload status is 'completed'.

**Parameters:**
- `session_id` (required): Upload session ID for a completed upload

**Example prompts:**
- "Get the result URL for my completed upload"
- "What's the final URL for upload session upload_abc123_1234567890?"

**Returns:**
- `session_id`: The upload session ID
- `url`: The fal.ai storage URL to use with models
- `file_size`: Size of the uploaded file

### 9. **cancel_upload**
Cancel an active upload operation. The background process will be terminated.

**Parameters:**
- `session_id` (required): Upload session ID to cancel

**Example prompts:**
- "Cancel my upload"
- "Stop upload session upload_abc123_1234567890"

**Returns:**
- `session_id`: The upload session ID
- `status`: 'cancelled' or 'already_finished'

### 10. **list_uploads**
List all upload sessions, optionally filtering to active ones only.

**Parameters:**
- `active_only` (optional): If True, only show active uploads. If False, show all uploads (default: False)

**Example prompts:**
- "Show all my uploads"
- "List only active uploads"
- "What files have I uploaded?"

**Returns:**
- `uploads`: List of upload sessions with status and progress
- `total_count`: Number of uploads returned
- `active_only`: Whether filtering was applied

### 11. **cleanup_old_uploads**
Clean up old upload state files to free disk space.

**Parameters:**
- `max_age_hours` (optional): Maximum age in hours for upload state files to keep (default: 24)

**Example prompts:**
- "Clean up upload files older than 48 hours"
- "Remove old upload state files"

**Returns:**
- `cleaned_count`: Number of state files removed
- `max_age_hours`: The age threshold used

### 12. **download_file**
Download a file from a URL to local filesystem.

**Parameters:**
- `url` (required): URL of the file to download (e.g., generated image or file)
- `filename` (optional): Optional filename to save as (will auto-detect from URL if not provided)
- `download_dir` (optional): Directory to download to (defaults to current directory if not provided)

**Example prompts:**
- "Download the generated image from https://fal.media/files/..."
- "Save this URL as output.png in my downloads folder"
- "Download the video to /home/user/videos/"

**Returns:**
- `filename`: Name of the downloaded file
- `file_path`: Full path to the downloaded file
- `size_bytes`: Size of the file in bytes
- `download_dir`: Directory where file was saved
- `url`: The source URL

## Queue Management Tools

### 13. **check_queue_status**
Check the status of an async job submitted to fal.ai.

**Parameters:**
- `model_id` (required): Model identifier used for the request
- `request_id` (required): Request ID returned from run_model with mode='submit'
- `with_logs` (optional): Whether to include execution logs (default: false)

**Example prompts:**
- "Check the status of request abc123 for flux model"
- "What's the progress of my video generation job?"
- "Get status with logs for request xyz789"

**Status values:**
- `queued`: Job is waiting in queue
- `inprogress`: Job is currently processing
- `completed`: Job finished successfully

### 14. **get_queue_result**
Get the result of a completed async job.

**Parameters:**
- `model_id` (required): Model identifier used for the request
- `request_id` (required): Request ID of the completed job

**Example prompts:**
- "Get the result of my completed image generation"
- "Fetch the output from request abc123"
- "Download the completed video from my job"

**Note:** Only works for jobs with status 'completed'

### 15. **cancel_queue_request**
Cancel a queued or running async job.

**Parameters:**
- `model_id` (required): Model identifier used for the request
- `request_id` (required): Request ID to cancel

**Example prompts:**
- "Cancel my running video generation job"
- "Stop the request abc123"
- "Cancel the queued image generation"

### 16. **list_queue_requests**
List all active async requests tracked in this session.

**Parameters:** None

**Example prompts:**
- "Show all my active jobs"
- "List my pending requests"
- "What jobs are currently running?"

**Returns:**
- List of active requests with their status, submission time, and last check time

## Common Usage Patterns

### Image Generation with Download Example
```
1. First, check what parameters FLUX needs:
   "Get the schema for fal-ai/flux/dev"

2. Generate an image:
   "Generate an image of a futuristic city at night with fal-ai/flux/dev"

3. Download the result:
   "Download the generated image to my desktop"
```

### File Upload Workflow Example
```
1. Upload a file (background process):
   "Upload my photo.jpg from the desktop"

2. Check upload progress:
   "Check the status of my upload"

3. Get the URL when complete:
   "Get the upload result"

4. Use with a model:
   "Enhance the uploaded image using an upscaling model"
```

### Async Job Management Example
```
1. Submit a long-running job:
   "Submit a video generation job with fal-ai/veo3"

2. Monitor progress:
   "Check status of my job"
   "List all my active requests"

3. Get result when done:
   "Get the result when completed"

4. Download the output:
   "Download the generated video"
```

### Model Discovery Workflow
```
1. Search for specific capabilities:
   "Search for video generation models"

2. Get details about a model:
   "Show me the schema for fal-ai/veo3"

3. Run the model:
   "Generate a 5-second video of a cat playing"
```

## Error Handling

All tools include comprehensive error handling:

- **Invalid Model ID**: Clear message about format requirements
- **Missing Parameters**: Lists which required parameters are missing
- **File Not Found**: Helpful error when files don't exist
- **File Too Large**: Error when files exceed 10MB limit
- **Upload Failures**: Automatic retry with exponential backoff
- **API Errors**: Passes through fal.ai error messages

## Best Practices

1. **Always check schemas first**: Use `get_model_schema` before running unfamiliar models
2. **Use async for everything**: All uploads use background processes to avoid timeouts
3. **Monitor uploads**: Use `check_upload_status` to track file upload progress
4. **Use async mode for long operations**: Video generation should use 'submit' mode
5. **Track your jobs**: Use `list_queue_requests` to monitor multiple operations
6. **Clean up periodically**: Use `cleanup_old_uploads` to free disk space
7. **Download results**: Use `download_file` to save generated content locally

## Upload System Architecture

The file upload system uses a background process architecture to handle uploads without MCP timeouts:

1. **Immediate Response**: Upload tools return a session ID immediately
2. **Background Processing**: Uploads happen in separate processes
3. **Progress Tracking**: Check status anytime with the session ID
4. **Persistent State**: Upload sessions survive MCP server restarts
5. **Automatic Retry**: Failed uploads retry up to 3 times
6. **10MB Limit**: Files larger than 10MB are rejected (fal.ai constraint)