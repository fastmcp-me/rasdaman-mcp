# Report: Rasdaman MCP Integration

## 1. Introduction to Micro-CLI Programs (MCPs)

Micro-CLI Programs (MCPs) serve as a powerful bridge, enabling Large Language Models (LLMs) to interact with external tools and services. This project utilizes the `fastmcp` framework to expose Rasdaman functionalities as a set of tools that an LLM can call to answer user queries in a natural language context.

### 1.1. How MCPs Function

The MCP server is designed with a flexible dual-mode architecture:

*   **`stdio` Mode (Managed):** This is the default mode, where a client like `gemini-cli` manages the server process. Communication occurs over standard input/output, providing a seamless and simple integration where tools are transparently available to the LLM.

*   **`http` Mode (Standalone):** The server can also run as a persistent, standalone web server. This mode is ideal for development, testing, or connecting with any HTTP-capable client. It uses a stateful JSON-RPC protocol that requires a three-step handshake to initialize a session before tools can be called. This decoupling allows the MCP server to function as an independent microservice.

## 2. Integrating MCPs with Rasdaman

The integration between the MCP framework and Rasdaman is achieved through a clean separation of concerns.

*   **`rasdaman_actions.py`:** This module acts as an abstraction layer. It contains the core logic for connecting to Rasdaman's Web Coverage Service (WCS) and Web Coverage Processing Service (WCPS) endpoints. It handles the specifics of forming queries and processing results, encapsulating the complexity of direct database interaction.

*   **`main.py`:** This script serves as the entry point for the MCP server. It uses the `fastmcp` framework to take the functions defined in `rasdaman_actions.py` and expose them as callable tools under the MCP protocol. This allows the LLM to invoke high-level functions without needing to know the underlying implementation details of the WCS/WCPS protocols.

## 3. Current Project Status

The initial phase of the project has successfully established a functional MCP-Rasdaman integration.

### 3.1. Implemented Tools

The following tools are currently available for an LLM to use:

*   **`list_coverages`:** Lists all available datacubes in the Rasdaman database.
*   **`describe_coverage`:** Retrieves structural metadata (e.g., bounding box, time steps) for a specific datacube.
*   **`execute_wcps_query`:** Executes a raw, user-provided WCPS query string.
*   **`calculate_ndvi`:** A specialized tool to calculate the Normalized Difference Vegetation Index (NDVI) for a Sentinel-2 coverage.

### 3.2. Documentation

Comprehensive documentation has been created to support the project:

*   **`README.md`:** Provides installation instructions and general usage guidelines.
*   **`docs/MCP_DESIGN.md`:** Outlines the architectural design of the MCP server.
*   **`docs/TECHNICAL_REFERENCE.md`:** Offers a detailed reference for the `rasdaman_actions.py` module.

## 4. Future Work and Enhancements

To build upon the current foundation, the following enhancements are proposed to make the toolset more powerful, robust, and safe for LLM interaction.

### 4.1. Higher-Level Abstraction for Complex Queries

While the `execute_wcps_query` tool is flexible, it requires the LLM to construct complex and potentially error-prone WCPS queries. The next step is to create higher-level, task-oriented tools that encapsulate common analytical workflows.

*   **Example:** Instead of asking an LLM to write a query for monthly NDVI, we can provide a tool like `get_monthly_ndvi_average(year: int, coverage_id: str)`.
*   **Benefit:** This reduces the cognitive load on the LLM, minimizes errors, and leads to more reliable and efficient execution of common tasks.

### 4.2. Enhanced Binary Data Handling

Rasdaman frequently returns binary data, such as PNG images or other file formats. The current implementation only identifies binary responses with a text message. This functionality should be enhanced to allow the LLM to directly retrieve and utilize this data.

*   **Proposed Improvement:** Modify the tools to return binary data as a Base64-encoded string within the JSON-RPC response or, alternatively, save the data to a temporary file and return its path.
*   **Benefit:** This will enable the LLM to handle images and other non-textual data, which is critical for many geospatial and scientific use cases.

### 4.3. Implementation of Safe and Unsafe Execution Modes

To mitigate the risk of accidental or unauthorized database modifications, a safety mechanism should be implemented.

*   **Safe Mode (Default):** The server would run in a read-only "safe" mode by default. In this mode, any tool or query that could modify data would be disabled.
*   **Unsafe Mode:** A specific command-line flag (e.g., `--unsafe`) would be required to start the server in a mode that permits write operations. This ensures that any database modifications are deliberate and authorized.
*   **Benefit:** This feature introduces a crucial layer of security, making it safer to expose the MCP tools to a wider range of clients and users.