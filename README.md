# PMIND fal.ai MCP Server

> ⚠️ **Experimental**: This MCP server is in an experimental state and may have rough edges. Please report any issues you encounter.

A Python implementation of the fal.ai MCP (Model Context Protocol) server using FastMCP. This server provides universal access to all fal.ai models without hardcoding specific model support, dynamically discovering model capabilities through OpenAPI schemas.

## 🎯 Features

This MCP server provides comprehensive access to fal.ai's AI model infrastructure with automatic schema discovery and validation.

### 📦 Core Capabilities

- **🤖 Universal Model Support**: Works with any current or future fal.ai model
- **🔍 Dynamic Schema Discovery**: Automatically fetches and validates model parameters
- **🚀 Multiple Execution Modes**: Support for synchronous, asynchronous, and subscription-based execution
- **📁 File Management**: Background upload system with progress tracking (no timeouts!)
- **⬇️ Download Support**: Download generated files and artifacts to local storage
- **📊 Queue Management**: Track and manage async jobs with status checking
- **💾 Schema Caching**: Improved performance through intelligent caching
- **✅ Automatic Validation**: Parameters are validated against model schemas before execution

### ✨ Key Features

- **🔐 API Key Authentication**: Secure access to fal.ai services
- **🎯 Smart Parameter Validation**: Only validates required parameters, allowing flexibility
- **📡 Comprehensive Error Handling**: Clear error messages with helpful context
- **🧠 Model Discovery**: List and search available models with pagination
- **📄 OpenAPI Integration**: Full schema access for understanding model requirements
- **⏱️ No Upload Timeouts**: Background process architecture handles large files seamlessly
- **📈 Upload Progress Tracking**: Monitor upload status with session-based tracking
- **🔄 Automatic Retry Logic**: Failed uploads retry with exponential backoff

## Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/pmind-fal-ai-mcp
cd pmind-fal-ai-mcp
```

### Step 2: Install Dependencies

```bash
# Install dependencies using uv
uv sync
```

### Step 3: Set Up fal.ai API Credentials

#### Get Your API Key
1. Go to [https://fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)
2. Sign in or create an account
3. Generate a new API key
4. Copy the key for use in configuration

### Step 4: Configure the Server

Create a `.env` file by copying the example:

```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
# fal.ai API Configuration
# Get your API key from https://fal.ai/dashboard/keys
FAL_API_KEY=your-api-key-here

# Cache directory for model schemas
# OpenAPI schemas are cached here to improve performance
FAL_CACHE_DIR=~/.pmind-fal-ai/cache

# Optional: Download directory for files (defaults to current directory)
# FAL_DOWNLOAD_DIR=/path/to/downloads

# Required: Upload state directory for async uploads
UPLOAD_STATE_DIR=/tmp/fal-uploads
```

### Step 5: Configure with Your Client

Add the MCP server to your client's MCP configuration:

```json
{
  "mcpServers": {
    "pmind-fal-ai": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/pmind-fal-ai-mcp", "pmind-fal-ai"]
    }
  }
}
```

Replace `/path/to/pmind-fal-ai-mcp` with the actual path where you cloned the repository.

#### For Claude Code (CLI)

Use the following command to add the server:

```bash
claude mcp add pmind-fal-ai -- uv run --directory /path/to/pmind-fal-ai-mcp pmind-fal-ai
```

## Configuration Options

### Environment Variables

Required:
- `FAL_API_KEY`: Your fal.ai API key for authentication
- `FAL_CACHE_DIR`: Directory for caching model schemas
- `UPLOAD_STATE_DIR`: Directory for upload state tracking

Optional:
- `FAL_DOWNLOAD_DIR`: Directory for downloaded files (defaults to current directory)

## Usage

Once configured, you can start using the fal.ai MCP server through your client. The server will automatically start when your client connects.

### Tool Reference
For a complete list of all tools with detailed parameters and examples, see [TOOLS.md](TOOLS.md).

### Example Usage

#### Generate an Image
```
Generate an image of a serene mountain landscape at sunset using FLUX
```

#### Run a Video Model
```
Generate a video of a cat playing with yarn using Veo3
```

#### Async Job Management
```
Submit a video generation job and check its status
```

#### Upload and Use Files
```
Upload my image.jpg and use it as input for image enhancement
```

#### Download Generated Files
```
Download the generated image from the URL to my local folder
```

### Manual Server Testing

To test the server manually:

```bash
# Run the MCP server
uv run pmind-fal-ai
```

## Troubleshooting

### Authentication Issues

- Ensure your `FAL_API_KEY` is set correctly in `.env`
- Verify the key at [https://fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)

### Model Not Found

- Use `list_models` to see available models
- Check the exact model ID with `search_models`

### Parameter Validation Errors

- Use `get_model_schema` to see required parameters
- Check parameter types and constraints in the schema
- Remember that only required parameters are validated

### Cache Issues

- Clear the cache directory if you encounter stale schema issues
- The cache directory is specified in `FAL_CACHE_DIR`

### Upload Issues

- Check upload status with `check_upload_status` using the session ID
- View all uploads with `list_uploads` to find lost sessions
- Clean up old uploads with `cleanup_old_uploads`
- Ensure files are under 10MB (fal.ai limit)
- Check `UPLOAD_STATE_DIR` for state files if debugging

## License

This project is licensed under the MIT License - see the LICENSE file for details.