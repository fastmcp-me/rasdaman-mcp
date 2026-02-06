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
        """
        logger.info(f"Executing WCPS: {wcps_query}")
        wcps_service = self.get_wcps_connection()
        try:
            # Explicitly URL-encode the WCPS query string
            encoded_wcps_query = urllib.parse.quote(wcps_query.encode("utf-8"))
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
