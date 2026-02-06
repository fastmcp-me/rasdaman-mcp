from wcs.service import WebCoverageService
from wcps.service import Service as WCPS_Service
from pydantic import BaseModel
from typing import List, Tuple
import os
import logging
import urllib.parse

# Configure Logging
logging.basicConfig(level=logging.INFO, stream=None)
logger = logging.getLogger("rasdaman_mcp")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)

# Configuration
RAS_HOST = os.getenv("RAS_IP", "192.168.122.179")
RAS_BASE = f"http://{RAS_HOST}:8080/rasdaman/ows"


def get_wcs_connection():
    """Helper to establish WCS connection."""
    try:
        return WebCoverageService(RAS_BASE)
    except Exception as e:
        logger.error(f"WCS Connection failed: {e}")
        raise RuntimeError(f"Failed to connect to Rasdaman at {RAS_BASE}")


def get_wcps_connection():
    """Helper to establish WCPS connection."""
    try:
        return WCPS_Service(RAS_BASE)
    except Exception as e:
        logger.error(f"WCPS Connection failed: {e}")
        raise RuntimeError(f"Failed to connect to Rasdaman at {RAS_BASE}")


def list_coverages_action() -> list[str]:
    """
    Lists all available datacubes (coverages) in the Rasdaman database.
    """
    wcs = get_wcs_connection()
    coverages = wcs.list_coverages()
    logger.info(f"Listed {len(coverages)} coverages.")
    return list(coverages.keys())


class CoverageMetadata(BaseModel):
    id: str
    bbox_wgs84: Tuple[float, float, float, float] | None
    timesteps: List[str]
    native_crs: str | None
    grid_axes: List[str] | str


def describe_coverage_action(coverage_id: str) -> CoverageMetadata:
    """
    Retrieves structural metadata for a specific datacube.
    """
    logger.info(f"Describing coverage: {coverage_id}")
    wcs = get_wcs_connection()

    basic_coverages = wcs.list_coverages()
    basic_cov = basic_coverages.get(coverage_id)
    if not basic_cov:
        raise ValueError(f"Coverage '{coverage_id}' not found")

    bbox_wgs84 = None
    if basic_cov.lon and basic_cov.lat:
        bbox_wgs84 = (
            basic_cov.lon.low,
            basic_cov.lat.low,
            basic_cov.lon.high,
            basic_cov.lat.high,
        )

    full_cov = wcs.list_full_info(coverage_id)

    timesteps = []
    if (
        full_cov.bbox
        and hasattr(full_cov.bbox, "ansi")
        and full_cov.bbox.ansi
        and full_cov.bbox.ansi.low
        and full_cov.bbox.ansi.high
    ):
        timesteps = [
            full_cov.bbox.ansi.low.isoformat(),
            full_cov.bbox.ansi.high.isoformat(),
        ]

    native_crs = str(full_cov.bbox.crs) if full_cov.bbox and full_cov.bbox.crs else None

    grid_axes = []
    if full_cov.grid_bbox:
        grid_axes = [axis.name for axis in full_cov.grid_bbox.axes]

    grid_axes_output = grid_axes if grid_axes else "Unknown"

    metadata = {
        "id": coverage_id,
        "bbox_wgs84": bbox_wgs84,
        "timesteps": timesteps,
        "native_crs": native_crs,
        "grid_axes": grid_axes_output,
    }
    return CoverageMetadata(**metadata)


def execute_wcps_query_action(wcps_query: str) -> str:
    """
    Executes a raw Web Coverage Processing Service (WCPS) query against the database.
    """
    logger.info(f"Executing WCPS: {wcps_query}")
    wcps_service = get_wcps_connection()
    try:
        # Explicitly URL-encode the WCPS query string
        encoded_wcps_query = urllib.parse.quote(wcps_query.encode('utf-8'))
        result = wcps_service.execute(encoded_wcps_query)
        try:
            # Try to decode as text
            decoded_value = result.value.decode("utf-8")
            return decoded_value
        except UnicodeDecodeError:
            # If decoding fails, assume it's binary data (image, netcdf, etc.)
            return f"Query executed successfully. Result is binary data ({len(result.value)} bytes)."

    except Exception as e:
        return f"WCPS Query Failed: {str(e)}"


def calculate_ndvi_action(coverage_id: str, time_slice: str = None) -> str:
    """
    Calculates the Normalized Difference Vegetation Index (NDVI) for a Sentinel-2 coverage.
    """
    if not time_slice:
        raise ValueError("time_slice is required for NDVI calculation.")

    # Extract only the date part (YYYY-MM-DD) from the time_slice
    date_part = time_slice.split("T")[0]
    query = f"""
    for c in ({coverage_id})
    return encode(
        (float)((c.B8[ansi("{date_part}")] - c.B4[ansi("{date_part}")]) / (c.B8[ansi("{date_part}")] + c.B4[ansi("{date_part}")])),
        "image/png"
    )
    """
    return execute_wcps_query_action(query)
