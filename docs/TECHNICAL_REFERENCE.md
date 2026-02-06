# Module: `rasdaman_actions.py` Technical Reference

This document provides a detailed technical reference for the `rasdaman_actions.py` module. This module has been refactored into a class-based structure to better manage configuration and state.

## `RasdamanActions` Class

This is the central class of the module, encapsulating all functionality for interacting with a Rasdaman server.

### Initialization

An instance of the class is created with the following parameters:

-   `__init__(self, rasdaman_url, username, password)`
    -   `rasdaman_url` (str): The full URL to the Rasdaman OWS endpoint (e.g., `http://localhost:8080/rasdaman/ows`).
    -   `username` (str): The username for authenticating with the Rasdaman server.
    -   `password` (str): The password for authentication.

### Methods

#### `get_wcs_connection()`
Helper method to establish a connection to the Rasdaman WCS endpoint using the credentials provided during class initialization.
-   **Returns**: An instance of `wcs.service.WebCoverageService`.
-   **Raises**: `RuntimeError` if the WCS connection fails.

#### `get_wcps_connection()`
Helper method to establish a connection to the Rasdaman WCPS endpoint using the credentials provided during class initialization.
-   **Returns**: An instance of `wcps.service.Service`.
-   **Raises**: `RuntimeError` if the WCPS connection fails.

#### `list_coverages_action()`
Lists all available datacubes (coverages) in the Rasdaman database.
-   **Returns**: A list of strings, where each string is the ID of an available coverage.

#### `describe_coverage_action(coverage_id: str)`
Retrieves structural metadata for a specific datacube.
-   **Parameters**:
    -   `coverage_id` (str): The ID of the coverage to describe.
-   **Returns**: A `CoverageMetadata` object.
-   **Raises**: `ValueError` if the specified `coverage_id` is not found.

#### `execute_wcps_query_action(wcps_query: str)`
Executes a raw Web Coverage Processing Service (WCPS) query.
-   **Parameters**:
    -   `wcps_query` (str): The WCPS query string to execute.
-   **Returns**: A string containing the query result or an error message.

#### `calculate_ndvi_action(coverage_id: str, time_slice: str)`
A specialized method to calculate the Normalized Difference Vegetation Index (NDVI).
-   **Parameters**:
    -   `coverage_id` (str): The ID of the Sentinel-2 coverage.
    -   `time_slice` (str): The date for the calculation (e.g., "2025-06-12").
-   **Returns**: The result from `execute_wcps_query_action`, typically a message indicating binary image data.
-   **Raises**: `ValueError` if `time_slice` is not provided.

## `CoverageMetadata` Pydantic Model
A Pydantic BaseModel defining the structure of the metadata returned by `describe_coverage_action`. This model is defined within the `rasdaman_actions.py` module.
-   `id`: The coverage ID.
-   `bbox_wgs84`: Bounding box coordinates.
-   `timesteps`: List of available time steps.
-   `native_crs`: The native Coordinate Reference System.
-   `grid_axes`: List of grid axes names.
