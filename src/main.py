from fastmcp import FastMCP
from rasdaman_actions import (
    list_coverages_action,
    describe_coverage_action,
    execute_wcps_query_action,
    calculate_ndvi_action,
    CoverageMetadata,
)

mcp = FastMCP("Rasdaman Geospatial Server")


@mcp.tool()
def list_coverages() -> list[str]:
    """
    Lists all available datacubes (coverages) in the Rasdaman database.
    Use this to discover available satellite datasets.
    """
    return list_coverages_action()


@mcp.tool()
def describe_coverage(coverage_id: str) -> CoverageMetadata:
    """
    Retrieves structural metadata for a specific datacube.
    Returns the bounding box (WGS84), time steps, and grid axes.
    """
    return describe_coverage_action(coverage_id)


@mcp.tool()
def execute_wcps_query(wcps_query: str) -> str:
    """
    Executes a raw Web Coverage Processing Service (WCPS) query against the database.
    Use this for custom band math, aggregation, or filtering.

    Example:
    for c in (Sentinel2_10m) return encode(c[ansi("2025-06-12")], "csv")
    """
    return execute_wcps_query_action(wcps_query)


@mcp.tool()
def calculate_ndvi(coverage_id: str, time_slice: str = None) -> str:
    """
    Calculates the Normalized Difference Vegetation Index (NDVI) for a Sentinel-2 coverage.
    """
    return calculate_ndvi_action(coverage_id, time_slice)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rasdaman MCP Server")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http"],
        default="stdio",
        help="The transport protocol to use.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="The port to use for the http transport.",
    )
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", port=args.port)
    else:
        mcp.run()
