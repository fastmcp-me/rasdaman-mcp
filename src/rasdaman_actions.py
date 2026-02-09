import io
import json
import logging
import tempfile
from typing import Any

import numpy as np
from PIL import Image
import netCDF4 as nc
from wcps.service import Service as WCPSConnection, WCPSResult, WCPSResultType
from wcs.service import WebCoverageService

from wcps_crash_course import wcps_crash_course

# Configure Logging
logging.basicConfig(level=logging.INFO, stream=None)
logger = logging.getLogger("rasdaman_mcp")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)


class RasdamanActions:
    def __init__(self, rasdaman_url, username, password):
        self.rasdaman_url = rasdaman_url
        self.username = username
        self.password = password

    def get_wcs_connection(self):
        """Helper to establish WCS connection."""
        try:
            return WebCoverageService(self.rasdaman_url, username=self.username, password=self.password)
        except Exception as e:
            logger.error(f"WCS Connection failed: {e}")
            raise RuntimeError(f"Failed to connect to Rasdaman at {self.rasdaman_url}")

    def get_wcps_connection(self):
        """Helper to establish WCPS connection."""
        try:
            return WCPSConnection(self.rasdaman_url, username=self.username, password=self.password)
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

    def describe_coverage_action(self, coverage_id: str) -> str:
        """
        Retrieves structural metadata for a specific datacube.
        """
        logger.info(f"Describing coverage: {coverage_id}")
        wcs = self.get_wcs_connection()
        full_cov = wcs.list_full_info(coverage_id)
        return str(full_cov)

    def wcps_query_crash_course_action(self) -> str:
        """
        Returns a crash course on writing WCPS queries.
        """
        logger.info(f"Returning WCPS crash course.")
        return wcps_crash_course

    def execute_wcps_query_action(self, wcps_query: str) -> Any:
        """
        Executes a WCPS query in rasdaman using the wcps-python-client library.
        """
        logger.info(f"Executing WCPS query: {wcps_query}")

        wcps_service = self.get_wcps_connection()

        try:
            response: WCPSResult = wcps_service.execute(wcps_query)
            res_type = response.type

            if res_type in [WCPSResultType.SCALAR, WCPSResultType.MULTIBAND_SCALAR]:
                ret = str(response.value)
                logger.info(f"Returning scalar result: {ret}")
                return ret

            if res_type == WCPSResultType.JSON:
                json_str = json.dumps(response.value)
                save_threshold = 500
                if len(json_str) < save_threshold:
                    ret = json_str
                    logger.info(f"Returning JSON result: {ret}")
                    return ret

                # else result is too large, save as file and return first 500 chars
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmpfile:
                    tmpfile.write(json_str)
                    ret = f"JSON result saved in file {tmpfile.name}; first {save_threshold} chars: "
                    ret += json_str[0:save_threshold]
                    logger.info(ret)
                    return ret

            # at this point the result is some binary format -> save to a file first
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmpfile:
                tmpfile.write(response.value)
                ret = f"{res_type.capitalize()} result saved in file {tmpfile.name} of size {len(response.value)} bytes"

            if res_type == WCPSResultType.IMAGE:
                img = Image.open(io.BytesIO(response.value))
                width, height = img.size
                n_bands = len(img.getbands())
                arr = np.array(img)
                dtype = arr.dtype
                ret += f"; the result is an image of {width} x {height} pixels, {n_bands} bands of type {dtype}."
                logger.info(ret)
                return ret

            if res_type == WCPSResultType.NETCDF:
                with nc.Dataset("memory", mode="r", memory=response.value) as ds:
                    dimensions = {name: len(dim) for name, dim in ds.dimensions.items()}
                    variables = {}
                    for var_name, var in ds.variables.items():
                        if var_name in ds.dimensions:
                            continue
                        variables[var_name] = {
                            "type": var.dtype,
                            "shape": var.shape,
                            "dimensions": var.dimensions,
                            "attributes": dict(var.__dict__),
                        }
                    ret += f"dimensions: {dimensions}; variables: {variables}"
                logger.info(ret)
                return ret

            # Non-encoded raw array
            logger.info(ret)
            return ret

        except Exception as e:
            ret = f"WCPS query failed: {str(e)}"
            logger.exception(ret)
            return ret
