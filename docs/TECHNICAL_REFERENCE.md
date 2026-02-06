# Module: `rasdaman_actions.py` Technical Reference

This document provides a detailed technical reference for the `rasdaman_actions.py` module. This module contains functions that abstract away direct interaction with the Rasdaman OWS (Open Geospatial Consortium Web Services) endpoints, providing a Python interface for the Web Coverage Service (WCS) and Web Coverage Processing Service (WCPS).

## Configuration

-   `RAS_HOST`: The IP address of the Rasdaman server. Configurable via the `RAS_IP` environment variable, defaults to `192.168.122.179`.
-   `RAS_BASE`: The base URL for the Rasdaman OWS endpoint, constructed dynamically using `RAS_HOST`.

## Functions

#### `get_wcs_connection()`
Helper function to establish a connection to the Rasdaman WCS endpoint.
-   **Returns**: An instance of `wcs.service.WebCoverageService`.
-   **Raises**: `RuntimeError` if the WCS connection fails.

#### `get_wcps_connection()`
Helper function to establish a connection to the Rasdaman WCPS endpoint.
-   **Returns**: An instance of `wcps.service.Service`.
-   **Raises**: `RuntimeError` if the WCPS connection fails.

#### `list_coverages_action()`
Lists all available datacubes (coverages) in the Rasdaman database.
-   **Returns**: A list of strings, where each string is the ID of an available coverage.

#### `describe_coverage_action(coverage_id: str)`
Retrieves structural metadata for a specific datacube.
-   **Parameters**:
    -   `coverage_id` (str): The ID of the coverage to describe.
-   **Returns**: A `CoverageMetadata` object containing information such as:
    -   `id`: The coverage ID.
    -   `bbox_wgs84`: Bounding box coordinates in WGS84 (longitude, latitude).
    -   `timesteps`: List of available time steps for the coverage.
    -   `native_crs`: The native Coordinate Reference System of the coverage.
    -   `grid_axes`: List of grid axes names.
-   **Raises**: `ValueError` if the specified `coverage_id` is not found.

#### `execute_wcps_query_action(wcps_query: str)`
Executes a raw Web Coverage Processing Service (WCPS) query against the Rasdaman database.
The `wcps_query` string is explicitly URL-encoded before execution to ensure proper handling of special characters.
-   **Parameters**:
    -   `wcps_query` (str): The WCPS query string to execute.
-   **Returns**: A string. If the result is decodable as UTF-8, the decoded string is returned. Otherwise, a message indicating binary data and its size is returned (e.g., "Query executed successfully. Result is binary data (12345 bytes).").

#### `calculate_ndvi_action(coverage_id: str, time_slice: str)`
Calculates the Normalized Difference Vegetation Index (NDVI) for a Sentinel-2 coverage.
This function constructs and executes a WCPS query to compute NDVI.
-   **Parameters**:
    -   `coverage_id` (str): The ID of the Sentinel-2 coverage (e.g., `s2_10m`).
    -   `time_slice` (str): The specific time slice for which to calculate NDVI. Only the `YYYY-MM-DD` part is extracted from this string for use in the `ansi()` WCPS function.
-   **Returns**: A string representing the result of the `execute_wcps_query_action`, which will typically be a message indicating binary data (the PNG image of NDVI) and its size upon successful execution.
-   **Raises**: `ValueError` if `time_slice` is not provided.

## `CoverageMetadata` Pydantic Model
A Pydantic BaseModel defining the structure of the metadata returned by `describe_coverage_action`.
