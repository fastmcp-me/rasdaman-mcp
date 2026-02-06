# Rasdaman MCP Server: Overview and Design

This document outlines the design for a Model Context Protocol (MCP) server that acts as a bridge between Large Language Models (LLMs) and a Rasdaman database.

## 1. Overview

The primary goal is to enable LLMs to interact with Rasdaman in a natural language context. By exposing Rasdaman functionalities as tools via the MCP protocol, an LLM can query the database to answer questions like:

- "What datacubes are available?"
- "What are the dimensions of the 'Sentinel2_10m' coverage?"
- "Generate an NDVI image for June 12, 2025."

The MCP server translates these tool calls into actual WCS/WCPS queries that Rasdaman can understand and then returns the results to the LLM.

## 2. Architectural Design

The architecture is designed to support two primary modes of operation, ensuring both ease of use and flexibility.

### 2.1. Dual-Mode Operation

The server can be run in two ways:

**a) Standalone Mode:**

The server can be started as a persistent, standalone HTTP server by running the main script with the appropriate command-line arguments.

```bash
# Run the server in HTTP mode on port 8000
python3 src/main.py --transport http --port 8000
```

This launches a `uvicorn` server that listens on the specified port.

**Benefits:**
- **Decoupling:** Any client that can speak HTTP (e.g., `curl`, Python scripts, web apps, other LLM clients) can interact with the tools.
- **Testing:** Allows for direct API testing and debugging, independent of an LLM client.
- **Scalability:** The server can be containerized (e.g., with Docker) and deployed as a separate microservice.

**b) Managed Mode (`stdio`):**

The server can be managed by a client like `gemini-cli`. This is the default behavior when running `python3 src/main.py` without arguments.
```bash
# This uses the default stdio transport
gemini mcp add src/main.py
```
In this mode, the client communicates with the server over standard input/output (`stdio`) instead of HTTP.

**Benefits:**
- **Simplicity:** No need to manage a separate server process or ports.
- **Seamless Integration:** Tools are transparently made available to the LLM within the client environment.

### 2.2. Core Components

- **FastMCP (`mcp`):** The core framework used to define and expose the tools. It is built on top of FastAPI.
- **Tool Functions (`rasdaman_actions.py`):** These are the Python functions that contain the actual logic for interacting with the Rasdaman WCS/WCPS endpoints.
- **Main Application (`main.py`):** This script initializes the FastMCP application, handles command-line arguments for transport selection, and decorates the tool functions.

## 3. Defined Tools

The following functions from `rasdaman_actions.py` are exposed as tools. Note that when calling them via the `tools/call` RPC method, the arguments are passed in a nested `arguments` object.

- **`list_coverages()`**: Lists all available datacubes.
- **`describe_coverage(coverage_id: str)`**: Retrieves metadata for a specific datacube.
- **`execute_wcps_query(wcps_query: str)`**: Executes a raw WCPS query.
- **`calculate_ndvi(coverage_id: str, time_slice: str)`**: Calculates the NDVI for a given Sentinel-2 coverage and time.

## 4. Testing the Standalone Server

Interacting with the standalone HTTP server requires a specific 3-step process using `curl`. The `fastmcp` protocol is stateful and requires a session to be explicitly initialized.

### Step 1: Initialize Session

First, send an `initialize` request. This will return a `200 OK` response and, most importantly, a session ID in the `mcp-session-id` response header.

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
*Extract the `mcp-session-id` from the response headers for the next steps.*

### Step 2: Send Initialized Notification

Next, send a notification to the server to confirm the session is ready. Use the session ID from Step 1 in the `Mcp-Session-Id` header. This request will not produce a body in the response.

```bash
# Replace <YOUR_SESSION_ID> with the ID from Step 1
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

### Step 3: Call a Tool

Finally, you can call a tool using the `tools/call` method. The `params` object must contain the `name` of the tool and an `arguments` object with the parameters for that tool.

```bash
# Replace <YOUR_SESSION_ID> with the ID from Step 1
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
The server will respond with the result of the tool call in a JSON-RPC response.
