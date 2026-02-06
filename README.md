# Rasdaman MCP Integration Project

This project provides a set of Model Context Protocol (MCP) tools for interacting with a Rasdaman Web Coverage Service (WCS) and Web Coverage Processing Service (WCPS). It allows users to list coverages, describe their metadata, execute raw WCPS queries, and specifically calculate the Normalized Difference Vegetation Index (NDVI) for Sentinel-2 data.

## Table of Contents

-   [[#installation | Installation]]
-   [[#usage | Usage]]
-   [[#documentation | Documentation]]

## Installation

This project requires Python 3.14. It is highly recommended to use a virtual environment.

1.  **Create a virtual environment** (if you don't have one):
    ```bash
    python3.14 -m venv venv
    ```

2.  **Activate the virtual environment**:
    ```bash
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    The core dependencies for this project are `fastmcp`, `python-wcs`, `python-wcps`, `pydantic`, `typer`, and `uvicorn`. While `fastmcp` often brings in `typer` and `uvicorn`, explicit installation ensures all necessary packages are present.

    ```bash
    pip install fastmcp wcs wcps pydantic typer uvicorn
    ```

    //Note: wcs and wcps are specific client libraries for WCS and WCPS interactions, often found in geospatial contexts. Ensure these are the correct packages for your Rasdaman setup.//

4.  **Deactivate the virtual environment** when you're done:
    ```bash
    deactivate
    ```

## Usage

This project can be run in two primary modes, controlled by the `--transport` command-line argument. The connection to the Rasdaman server can be configured via command-line arguments, which override any environment variables.

### Configuration Arguments
-   `--rasdaman-url`: Sets the URL for the Rasdaman server. Defaults to the `RASDAMAN_URL` environment variable or `http://localhost:8080/rasdaman/ows`.
-   `--username`: Sets the username for authentication. Defaults to the `RASDAMAN_USERNAME` environment variable or `rasguest`.
-   `--password`: Sets the password for authentication. Defaults to the `RASDAMAN_PASSWORD` environment variable or `rasguest`.

#### Environment Variables

Environment variables for configuring the connection to the rasdaman instance:

| Variable | Description | Default |
| `RASDAMAN_URL` | Base URL of the rasdaman service | `http://localhost:8080/rasdaman/ows` |
| `RASDAMAN_USERNAME` | Username for authentication | `rasguest` |
| `RASDAMAN_PASSWORD` | Password for authentication | `rasguest` |

### `stdio` Mode (Default)

This mode is used for direct integration with clients like `gemini-cli` (an example) that manage the server process. It uses standard input/output for communication.

To add an MCP tool to your client, use the following general syntax:
`gemini mcp add [mcp-name] [mcp-execution-command]`

1.  **Add the tool to your client:**
    ```bash
    gemini mcp add rasdaman-mcp "<path-to-your-python-env> <path-to-your-main.py> --username myuser --password mypass"
    ```
    //Note: You must use absolute paths to your python environment (e.g., `/path/to/your/project/venv/bin/python`) and the `main.py` script (e.g., `/path/to/your/project/src/main.py`).//

2.  **Use the tools via the client:** The LLM can now use the functions (`list_coverages`, `describe_coverage`, etc.) as tools.

### Standalone `http` Mode

This mode runs a persistent web server, which is useful for development, testing, or connecting with other types of clients.

1.  **Run the server:**
    ```bash
    <path-to-your-python-env> <path-to-your-main.py> --transport http --port 8000 --rasdaman-url "http://my-rasdaman:8080/rasdaman/ows"
    ```
    //Note: You must use absolute paths to your python environment and the `main.py` script.//

    The server will now be listening on `http://127.0.0.1:8000`.

2.  **Interact with the server:** You can now send JSON-RPC requests to the server to call the tools.

### Testing the Standalone Server

The `http` server uses a stateful, stream-based protocol that requires a specific 3-step process to interact with it using a tool like `curl`.

For detailed instructions and `curl` examples on how to test the standalone server, please refer to the **[[docs/MCP_DESIGN.md | MCP Server Design and Testing Document]]**.

## Documentation

Comprehensive documentation for the `rasdaman_actions.py` module, its functions, and their integration into the MCP framework can be found here:

-   [[docs/TECHNICAL_REFERENCE.md | Rasdaman MCP Integration Documentation]]
