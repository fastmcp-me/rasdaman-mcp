import io
import json
import logging
import tempfile
import time
from typing import Any

import netCDF4 as nc
import numpy as np
from PIL import Image
from wcps.service import Service as WCPSConnection, WCPSResult, WCPSResultType
from wcs.service import WebCoverageService

from .wcps_crash_course import WCPS_CRASH_COURSE

logger = logging.getLogger()


class Timer:
    """Simple timer for logging execution time."""
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()

    @property
    def elapsed(self):
        if self.start_time is None:
            return None
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time

    def log(self, msg=""):
        if self.start_time is None:
            return
        elapsed = self.elapsed
        full_msg = f"{msg} in {elapsed:.3f}s"
        logger.info(full_msg)


class RasdamanActions:
    def __init__(self, rasdaman_url, username, password):
        self.rasdaman_url = rasdaman_url
        self.username = username
        self.password = password
        self.wcs_service = WebCoverageService(rasdaman_url, username=username, password=password)
        self.wcps_service = WCPSConnection(rasdaman_url, username=username, password=password)

    def list_coverages_action(self) -> list[str]:
        """
        Lists all available datacubes (coverages) in the rasdaman database.
        """
        logger.info(f"Listing coverages in rasdaman...")
        with Timer() as timer:
            coverages = self.wcs_service.list_coverages()
            ret = list(coverages.keys())
            timer.log(f"Listed {len(coverages)} coverages")
        return ret

    def describe_coverage_action(self, coverage_id: str) -> str:
        """
        Retrieves structural metadata for a specific datacube.
        """
        logger.info(f"Describing coverage: {coverage_id}")
        with Timer() as timer:
            full_cov = self.wcs_service.list_full_info(coverage_id)
            ret = str(full_cov)
            timer.log(f"Done getting description for {coverage_id}")
        return ret

    def wcps_query_crash_course_action(self) -> str:
        """
        Returns a crash course on writing WCPS queries.
        """
        logger.info(f"Returning WCPS crash course.")
        return WCPS_CRASH_COURSE

    def execute_wcps_query_action(self, wcps_query: str) -> Any:
        """
        Executes a WCPS query in rasdaman using the wcps-python-client library.
        """
        logger.info(f"Executing WCPS query: {wcps_query}")

        # 1. execute the WCPS query
        try:
            with Timer() as timer:
                response: WCPSResult = self.wcps_service.execute(wcps_query)
                timer.log(f"Executed WCPS query")
            res_type = response.type
        except Exception as e:
            ret = f"Executing WCPS query failed: {str(e)}"
            logger.exception(ret)
            return ret

        # 2. interpret the result in order to return a more meaningful response to the LLM
        try:
            # scalars: returned directly
            if res_type in [WCPSResultType.SCALAR, WCPSResultType.MULTIBAND_SCALAR]:
                ret = str(response.value)
                logger.info(f"Returning scalar result: {ret}")
                return ret

            # JSON: return trimmed to 500 chars, if larger also save as temp file
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

            # 2D images: return filepath + image metadata
            if res_type == WCPSResultType.IMAGE:
                img = Image.open(io.BytesIO(response.value))
                width, height = img.size
                n_bands = len(img.getbands())
                arr = np.array(img)
                dtype = arr.dtype
                ret += f"; the result is an image of {width} x {height} pixels, {n_bands} bands of type {dtype}."
                logger.info(ret)
                return ret

            # NetCDF: return filepath + image metadata
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
            ret = f"Failed handling WCPS query result: {str(e)}"
            logger.exception(ret)
            return ret
