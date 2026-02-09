from fastmcp import FastMCP
from rasdaman_actions import RasdamanActions
import os
import argparse
from typing import Any

mcp = FastMCP(
    name="Rasdaman MCP Server",
    instructions="This server provides access to a rasdaman instance: list coverages, get coverage details, and execute a WCPS query.",
)

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
    "--host",
    type=str,
    default="127.0.0.1",
    help="The host to use for the http transport.",
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
    Lists all available datacubes (coverages) in rasdaman.
    """
    return ras_actions.list_coverages_action()


@mcp.tool()
def describe_coverage(coverage_id: str) -> str:
    """
    Retrieves structural metadata for a specific datacube (coverage).
    """
    return ras_actions.describe_coverage_action(coverage_id)


@mcp.tool()
def wcps_query_crash_course() -> str:
    """
    Returns a crash course on writing WCPS queries:
    learn the basic syntax, common operations, and best practices for WCPS queries.
    It's recommended to check this before executing queries.
    """
    return ras_actions.wcps_query_crash_course_action()


@mcp.tool()
def execute_wcps_query(wcps_query: str) -> Any:
    """
    Executes a Web Coverage Processing Service (WCPS) query in rasdaman.
    Use this for spatio-temporal subsetting of datacubes, processing, aggregation, or filtering.
    If the query returns binary data (e.g., an image or NetCDF file),
    the tool saves it to a temporary file and return the path.
    **Important:** before calling the tool, show the actual WCPS query to the user.

    Example query:
    for c in (Sentinel2_10m) return encode((unsigned char) (c[ansi("2025-06-12")].B04 / 10.0), "png")
    """
    return ras_actions.execute_wcps_query_action(wcps_query)


if __name__ == "__main__":
    if args.transport == "http":
        mcp.run(transport="http", port=args.port, host=args.host)
    else:
        mcp.run()
