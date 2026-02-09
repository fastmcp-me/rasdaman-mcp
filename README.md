# Rasdaman MCP Server

This tool enables users to interact with rasdaman in a natural language context.
By exposing rasdaman functionality as tools via the MCP protocol, an LLM can query the database to answer questions like:

- "What datacubes are available?"
- "What are the dimensions of the 'Sentinel2_10m' coverage?"
- "Create an NDVI image for June 12, 2025."

The MCP server translates these tool calls into actual WCS/WCPS queries that rasdaman can understand and then returns the results to the LLM.

## Setup

1.  **Create a virtual environment** (if you don't have one):
    ```bash
    uv venv
    ```

2.  **Activate the virtual environment**:
    ```bash
    source .venv/bin/activate
    ```

3.  **Install dependencies** (`fastmcp < 3`, `wcs`, `wcps`, `Pillow`, `netCDF4`, `requests`)
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Deactivate the virtual environment** when done:
    ```bash
    deactivate
    ```

## Usage

The entry point is `src/main.py`. It can be run in two primary modes controlled by the `--transport` command-line argument: `stdio` (default) and `http`.

In the examples below, `${PROJECT_PATH}` refers to the absolute path of this project.

### Configuration
The connection from the MCP server to rasdaman can be configured in two ways.

1. Command-line arguments:
 - `--rasdaman-url`: URL for the rasdaman server (default `RASDAMAN_URL` environment variable or `http://localhost:8080/rasdaman/ows`).
 - `--username`: Username for authentication (default `RASDAMAN_USERNAME` environment variable or `rasguest`).
 - `--password`: Sets the password for authentication (default `RASDAMAN_PASSWORD` environment variable or `rasguest`).

2. Environment variables:
 - `RASDAMAN_URL`: URL for the rasdaman server
 - `RASDAMAN_USERNAME`: Username for authentication
 - `RASDAMAN_PASSWORD`: Password for authentication

### `stdio` Mode
Used for direct integration with clients that take over managing the server process. It uses standard input/output for communication.
Generally in your client configuration you need to specify the command to run the MCP tool:

    python3 ${PROJECT_PATH}/src/main.py --username rasguest --password rasguest

Keep in mind that all dependencies are installed, and the venv is activated if necessary.

Example for gemini-cli:

    gemini mcp add rasdaman-mcp "${PROJECT_PATH}/.venv/bin/python ${PROJECT_PATH}/src/main.py --username rasguest --password rasguest"

Benefits:
- Simplicity: No need to manage a separate server process or ports.
- Seamless Integration: Tools are transparently made available to the LLM within the client environment.

### `http` Mode
This mode runs a standalone Web server.

1. Start the server:

        .venv/bin/python src/main.py --transport http --host 127.0.0.1 --port 8000 --rasdaman-url "http://localhost:8080/rasdaman/ows"

2. Configure your client to add an MCP server at `http://127.0.0.1:8000/mcp`. For example, for 
   Mistral Vibe extend the config.toml with a section like this:

        [[mcp_servers]]
        name = "rasdaman_mcp"
        transport = "streamable-http"
        url = "http://127.0.0.1:8000/mcp/"

Benefits:
- Scalability: The MCP server can be containerized (e.g., with Docker) and deployed as a separate microservice.
- Decoupling: Any client that can speak HTTP (e.g., `curl`, Python scripts, web apps, other LLM clients) can interact with the tools.
- Testing: Allows for direct API testing and debugging, independent of an LLM client.


## Development

### Core Components

- Main Application (`main.py`): This script initializes the FastMCP application. It handles command-line arguments for transport selection, rasdaman URL,
  username, and password. It then instantiates the `RasdamanActions` class and decorates its methods to expose them as tools.
- `RasdamanActions` Class (`rasdaman_actions.py`): Encapsulates all interaction with the rasdaman WCS/WCPS endpoints.
  It is initialized with the server URL and credentials, and its methods contain the logic for listing coverages, describing them, and executing queries.
- WCPS Crash Course (`wcps_crash_course.py`): A short summary of the syntax of WCPS, allowing LLMs to generate more accurate queries.

### 3. Defined Tools

The following methods are exposed as tools:
- `list_coverages()`: Lists all available datacubes.
- `describe_coverage(coverage_id)`: Retrieves metadata for a specific datacube.
- `wcps_query_crash_course()`: Returns a crash course on WCPS syntax with examples and best practices.
- `execute_wcps_query(wcps_query)`: Executes a raw WCPS query and returns a result either directly as a string (scalars or small json), or as a filepath.

### Testing

Interacting with the standalone HTTP server *manually* requires a specific 3-step process using `curl`.
The `fastmcp` protocol is stateful and requires a session to be explicitly initialized.

1. First, send an `initialize` request. This will return a `200 OK` response and, most importantly, 
   a session ID in the `mcp-session-id` response header (needed in the next steps).
```bash
curl -i -X POST \
-H "Accept: text/event-stream, application/json" \
-H "Content-Type: application/json" \
-d '{
      "jsonrpc": "2.0",
      "method": "initialize",
      "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": { "name": "curl-client", "version": "1.0.0" }
      },
      "id": 1
    }' \
"http://127.0.0.1:8000/mcp"
```

2. Next, send a notification to the server to confirm the session is ready. Use the session ID from Step 1 in the `mcp-session-id` header. 
   This request will not produce a body in the response.
```bash
SESSION_ID="<YOUR_SESSION_ID>"

curl -X POST \
-H "Accept: text/event-stream, application/json" \
-H "Content-Type: application/json" \
-H "Mcp-Session-Id: $SESSION_ID" \
-d '{
      "jsonrpc": "2.0",
      "method": "notifications/initialized"
    }' \
"http://127.0.0.1:8000/mcp"
```

3. Finally, you can call a tool using the `tools/call` method. The `params` object must contain the `name` of the tool and 
   an `arguments` object with the parameters for that tool. The server will respond with the result of the tool call in a JSON-RPC response.
```bash
SESSION_ID="<YOUR_SESSION_ID>"

# Example: Calling the 'list_coverages' tool
curl -X POST \
-H "Accept: text/event-stream, application/json" \
-H "Content-Type: application/json" \
-H "Mcp-Session-Id: $SESSION_ID" \
-d '{
      "jsonrpc": "2.0",
      "method": "tools/call",
      "params": {
        "name": "list_coverages",
        "arguments": {}
      },
      "id": 2
    }' \
"http://127.0.0.1:8000/mcp"
```
