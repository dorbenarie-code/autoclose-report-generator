from myapp.utils.logger_config import get_logger
from typing import Optional

log = get_logger(__name__)
logger = log
import pandas as pd
from pathlib import Path
from myapp.error_handler.base import FileFormatError
import logging


class XlsConverter:
    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = Path("uploads/converted") if temp_dir is None else temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def convert_to_xlsx(
        self, file_path: str, overwrite: bool = False, log_conversion: bool = True
    ) -> str:
        """
        Convert a .xls file to .xlsx and return the new file path.
        If the file is already .xlsx or has any other extension, returns the original path.
        If the converted file already exists and overwrite is False, skips conversion.

        Args:
            file_path (str): Path to the Excel file.
            overwrite (bool): If True, force reconversion even if the target exists.
            log_conversion (bool): If True, log a debug message when conversion occurs.

        Returns:
            str: Path to the converted .xlsx file, or the original path if no conversion is needed.

        Raises:
            FileFormatError: If reading the .xls file or writing the new .xlsx file fails.
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        # If not a .xls file, skip conversion
        if suffix != ".xls":
            return str(path)

        # Build the target .xlsx path
        new_filename = f"{path.stem}.converted.xlsx"
        new_path = self.temp_dir / new_filename

        # If target exists and we're not overwriting, skip
        if new_path.exists() and not overwrite:
            if log_conversion and self.logger:
                self.logger.debug(f"Skipped conversion; '{new_path}' already exists.")
            return str(new_path)

        # Step 1: Try to read the .xls file with xlrd
        try:
            df = pd.read_excel(path, engine="xlrd")
        except Exception as e_xlrd:
            if self.logger:
                self.logger.warning(f"❗ xlrd failed: {e_xlrd}")

            # Fallback: try default engine
            try:
                df = pd.read_excel(path)  # Let pandas decide the engine
                if self.logger:
                    self.logger.info("✅ Fallback to default engine succeeded.")
            except Exception as fallback_e:
                raise FileFormatError(
                    f"❌ Failed to read .xls file '{file_path}' with fallback: {fallback_e}"
                ) from fallback_e

        # Step 2: Write to .xlsx
        try:
            df.to_excel(new_path, index=False)
        except Exception as e:
            raise FileFormatError(
                f"❌ Failed to write .xlsx file '{new_path}': {e}"
            ) from e

        if log_conversion and self.logger:
            self.logger.debug(f"✅ Converted '{file_path}' to '{new_path}'.")

        return str(new_path)
