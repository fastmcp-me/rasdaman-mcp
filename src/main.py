from fastmcp import FastMCP
from rasdaman_actions import RasdamanActions, CoverageMetadata
import os
import argparse

mcp = FastMCP("Rasdaman Geospatial Server")

# Determine credentials
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
parser.add_argument(
    "--rasdaman-url",
    type=str,
    default=os.getenv("RASDAMAN_URL", "http://localhost:8080/rasdaman/ows"),
    help="URL of the Rasdaman server.",
)
parser.add_argument(
    "--username",
    type=str,
    default=os.getenv("RASDAMAN_USERNAME", "rasguest"),
    help="Username for authentication.",
)
parser.add_argument(
    "--password",
    type=str,
    default=os.getenv("RASDAMAN_PASSWORD", "rasguest"),
    help="Password for authentication.",
)
args = parser.parse_args()


# Instantiate RasdamanActions with credentials
ras_actions = RasdamanActions(
    rasdaman_url=args.rasdaman_url, username=args.username, password=args.password
)


@mcp.tool()
def list_coverages() -> list[str]:
    """
    Lists all available datacubes (coverages) in the Rasdaman database.
    Use this to discover available satellite datasets.
    """
    return ras_actions.list_coverages_action()


@mcp.tool()
def describe_coverage(coverage_id: str) -> CoverageMetadata:
    """
    Retrieves structural metadata for a specific datacube.
    Returns the bounding box (WGS84), time steps, and grid axes.
    """
    return ras_actions.describe_coverage_action(coverage_id)


@mcp.tool()
def execute_wcps_query(wcps_query: str) -> str:
    """
    Executes a raw Web Coverage Processing Service (WCPS) query against the database.
    Use this for custom band math, aggregation, or filtering.

    Example:
    for c in (Sentinel2_10m) return encode(c[ansi("2025-06-12")], "csv")
    """
    return ras_actions.execute_wcps_query_action(wcps_query)


if __name__ == "__main__":
    if args.transport == "http":
        mcp.run(transport="http", port=args.port)
    else:
        mcp.run()
