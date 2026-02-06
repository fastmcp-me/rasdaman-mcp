from wcs.service import WebCoverageService
from wcps.service import Service as WCPS_Service
from typing import List, Tuple, Any
import os
import logging
import tempfile
import mimetypes
import re
import sys
import subprocess

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

    def describe_coverage_action(self, coverage_id: str) -> str:
        """
        Retrieves structural metadata for a specific datacube.
        """
        logger.info(f"Describing coverage: {coverage_id}")
        wcs = self.get_wcs_connection()
        full_cov = wcs.list_full_info(coverage_id)
        return str(full_cov)

    def execute_wcps_query_action(self, wcps_query: str) -> Any:
        """
        Executes a Web Coverage Processing Service (WCPS) query against the database
        using the wcps-python-client library.
        """
        logger.info(f"Executing WCPS query: {wcps_query}")

        wcps_service = self.get_wcps_connection()
        output_format = None

        match = re.search(
            r'encode\s*\((?:.*,\s*)?["\']([^"\']+)["\']\s*\)', wcps_query, re.IGNORECASE
        )
        if match:
            output_format = match.group(1).lower()

        binary_formats = [
            "png",
            "jpeg",
            "gif",
            "tiff",
            "image/png",
            "image/jpeg",
            "image/gif",
            "image/tiff",
        ]

        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            if output_format and any(f in output_format for f in binary_formats):
                logger.info(
                    f"Detected binary output format '{output_format}'. Using download()."
                )
                suffix = mimetypes.guess_extension(output_format) or ".dat"
                if "." not in suffix:
                    suffix = "." + suffix

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix, mode="wb"
                ) as tmpfile:
                    file_path = tmpfile.name

                sys.stdout = open(os.devnull, "w")
                sys.stderr = open(os.devnull, "w")

                try:
                    wcps_service.download(wcps_query, output_file=file_path)

                    subprocess.Popen(["xdg-open", file_path])

                finally:
                    sys.stdout.close()
                    sys.stderr.close()
                    sys.stdout = original_stdout
                    sys.stderr = original_stderr

                result_obj = {"file_path": file_path}
                logger.info(f"Returning result: {result_obj}")
                return result_obj
            else:
                logger.info(
                    f"Detected text output format '{output_format or 'none specified'}'. Using execute()."
                )
                sys.stdout = open(os.devnull, "w")
                sys.stderr = open(os.devnull, "w")
                try:
                    result = wcps_service.execute(wcps_query)
                finally:
                    sys.stdout.close()
                    sys.stderr.close()
                    sys.stdout = original_stdout
                    sys.stderr = original_stderr

                text_result = result.value
                logger.info(f"Returning text result: {text_result[:100]}...")
                return text_result

        except Exception as e:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            logger.exception("WCPS Query Failed")
            return f"WCPS Query Failed: {str(e)}"
