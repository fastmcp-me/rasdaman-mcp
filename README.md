# Rasdaman MCP Server

This project provides a set of Model Context Protocol (MCP) tools for interacting with a Rasdaman Web Coverage Service (WCS) and Web Coverage Processing Service (WCPS). It allows users to list coverages, describe their metadata, and execute WCPS queries.

## Table of Contents

-   [[#installation | Installation]]
-   [[#usage | Usage]]
-   [[#documentation | Documentation]]

## Setup

1.  **Create a virtual environment** (if you don't have one):
    ```bash
    python3.14 -m venv .venv
    ```

2.  **Activate the virtual environment**:
    ```bash
    source .venv/bin/activate
    ```

3.  **Install dependencies** (`fastmcp`, `python-wcs`, `python-wcps`, `pydantic`, `typer`, `uvicorn`, `Pillow`, `netCDF4`)
    ```bash
    pip install -r requirements.txt
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
 - `--rasdaman-url`: Sets the URL for the rasdaman server (default `RASDAMAN_URL` environment variable or `http://localhost:8080/rasdaman/ows`).
 - `--username`: Sets the username for authentication (default `RASDAMAN_USERNAME` environment variable or `rasguest`).
 - `--password`: Sets the password for authentication (default `RASDAMAN_PASSWORD` environment variable or `rasguest`).

2. Environment variables:
 - `RASDAMAN_URL`: Sets the URL for the rasdaman server (default `http://localhost:8080/rasdaman/ows`)
 - `RASDAMAN_USERNAME`: Username for authentication (default `rasguest`)
 - `RASDAMAN_PASSWORD`: Password for authentication (default `rasguest`)


### `stdio` Mode
Used for direct integration with clients like `gemini-cli` (an example) that take over managing the server process. It uses standard input/output for communication.

To add an MCP tool to your client, use the following general syntax: `gemini mcp add [mcp-name] [mcp-execution-command]`

1.  **Add the tool to your client:**
    ```bash
    gemini mcp add rasdaman-mcp "${PROJECT_PATH}/.venv/bin/python ${PROJECT_PATH}/src/main.py --username rasguest --password rasguest"
    ```

2.  **Use the tools via the client:** The LLM can now use the functions (`list_coverages`, `describe_coverage`, etc.) as tools.

### `http` Mode
This mode runs a separate web server, which is useful for development, testing, or allowing multiple clients to connect to it over the network.

1.  **Start the server:**
    ```bash
    ${PROJECT_PATH}/.venv/bin/python ${PROJECT_PATH}/src/main.py --transport http --port 8000 --rasdaman-url "http://localhost:8080/rasdaman/ows"
    ```
    The server will now be listening on `http://127.0.0.1:8000`.

2.  **Interact with the server:** You can now send JSON-RPC requests to the server to call the tools.

## Testing

### `http` Mode

The `http` server uses a stateful, stream-based protocol that requires a specific 3-step process to interact with it using a tool like `curl`.

For detailed instructions and `curl` examples, please refer to the **[[docs/MCP_DESIGN.md | MCP Server Design and Testing Document]]**.

## Documentation

Comprehensive documentation for the `rasdaman_actions.py` module, its functions, and their integration into the MCP framework can be found here:

-   [[docs/TECHNICAL_REFERENCE.md | Rasdaman MCP Integration Documentation]]
