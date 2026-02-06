from wcs.service import WebCoverageService
from wcps.service import Service as WCPS_Service
from pydantic import BaseModel
from typing import List, Tuple
import os
import logging
import urllib.parse
import tempfile
import mimetypes
import re

# Configure Logging
logging.basicConfig(level=logging.INFO, stream=None)
logger = logging.getLogger("rasdaman_mcp")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)


class CoverageMetadata(BaseModel):
    id: str
    bbox_wgs84: Tuple[float, float, float, float] | None
    timesteps: List[str]
    native_crs: str | None
    grid_axes: List[str] | str


class RasdamanActions:
    def __init__(self, rasdaman_url, username, password):
        self.rasdaman_url = rasdaman_url
        self.username = username
        self.password = password

    def get_wcs_connection(self):
        """Helper to establish WCS connection."""
        try:
            return WebCoverageService(
                self.rasdaman_url, username=self.username, password=self.password
            )
        except Exception as e:
            logger.error(f"WCS Connection failed: {e}")
            raise RuntimeError(f"Failed to connect to Rasdaman at {self.rasdaman_url}")

    def get_wcps_connection(self):
        """Helper to establish WCPS connection."""
        try:
            return WCPS_Service(
                self.rasdaman_url, username=self.username, password=self.password
            )
        except Exception as e:
            logger.error(f"WCPS Connection failed: {e}")
            raise RuntimeError(f"Failed to connect to Rasdaman at {self.rasdaman_url}")

    def list_coverages_action(self) -> list[str]:
        """
        Lists all available datacubes (coverages) in the Rasdaman database.
        """
        wcs = self.get_wcs_connection()
        coverages = wcs.list_coverages()
        logger.info(f"Listed {len(coverages)} coverages.")
        return list(coverages.keys())

    def describe_coverage_action(self, coverage_id: str) -> CoverageMetadata:
        """
        Retrieves structural metadata for a specific datacube.
        """
        logger.info(f"Describing coverage: {coverage_id}")
        wcs = self.get_wcs_connection()

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

        native_crs = (
            str(full_cov.bbox.crs) if full_cov.bbox and full_cov.bbox.crs else None
        )

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

    def execute_wcps_query_action(self, wcps_query: str) -> str:
        """
        Executes a raw Web Coverage Processing Service (WCPS) query against the database.
        Streams the response to handle large datasets efficiently.
        """
        logger.info(f"Executing WCPS query via direct URL request: {wcps_query}")

        try:
            # Manually construct the GET request URL
            params = {
                "service": "WCS",
                "version": "2.0.1",
                "request": "ProcessCoverages",
                "query": wcps_query,
            }
            encoded_params = urllib.parse.urlencode(params)

            base_url = self.rasdaman_url.rstrip("?&")
            request_url = f"{base_url}?{encoded_params}"

            logger.info(f"Request URL: {request_url}")

            with urllib.request.urlopen(request_url, timeout=60) as response:
                info = response.info()
                content_type = info.get("Content-Type", "application/octet-stream")
                logger.info(f"Response Content-Type: {content_type}")

                # Check if content is text-based
                if (
                    "text" in content_type
                    or "xml" in content_type
                    or "json" in content_type
                ):
                    logger.info("Handling as text response.")
                    result = response.read().decode("utf-8")
                    logger.info(
                        f"Returning text result: {result[:100]}"
                    )  # Log first 100 chars
                    return result

                logger.info("Handling as binary response.")
                suffix = mimetypes.guess_extension(content_type) or ".dat"

                match = re.search(
                    r'encode\s*\([^,]+,\s*["\'](\w+)["\']\s*\)',
                    wcps_query,
                    re.IGNORECASE,
                )
                if match:
                    format_from_query = match.group(1).lower()
                    if not format_from_query.startswith("."):
                        format_from_query = "." + format_from_query
                    suffix = format_from_query

                logger.info(f"Using file suffix: {suffix}")

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix, mode="wb"
                ) as tmpfile:
                    chunk_size = 8192
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        tmpfile.write(chunk)

                    file_path = tmpfile.name
                    logger.info(f"Streamed binary data to temporary file: {file_path}")
                    result_str = f"Binary data saved to: {file_path}"
                    logger.info(f"Returning result: {result_str}")
                    return result_str

        except urllib.error.HTTPError as e:
            error_content = e.read().decode("utf-8") if e.readable() else e.reason
            logger.error(f"HTTP Error {e.code}: {error_content}")
            return f"WCPS Query Failed with HTTP Error {e.code}: {error_content}"
        except Exception as e:
            logger.exception("WCPS Query Failed")
            return f"WCPS Query Failed: {str(e)}"
