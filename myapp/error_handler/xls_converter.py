import logging
import pandas as pd
from pathlib import Path
from .base import FileFormatError


class XlsConverter:
    """
    Utility to convert legacy Excel files (.xls) to .xlsx.
    If the input is not an .xls file, it is returned unchanged.
    """

    def __init__(self, temp_dir: Path = None):
        """
        Args:
            temp_dir (Path): Directory where converted files are stored.
        """
        if temp_dir is None:
            temp_dir = Path("uploads/converted")
        self.temp_dir = temp_dir
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

        # No conversion needed if not .xls
        if suffix != ".xls":
            if log_conversion:
                self.logger.debug(f"No conversion needed for '{file_path}'.")
            return str(path)

        # Determine the target path
        new_filename = f"{path.stem}.converted.xlsx"
        new_path = self.temp_dir / new_filename

        # If target exists and overwrite is False, skip conversion
        if new_path.exists() and not overwrite:
            if log_conversion:
                self.logger.debug(f"Skipped conversion; '{new_path}' already exists.")
            return str(new_path)

        # Step 1: Read the old .xls file
        try:
            df = pd.read_excel(path, engine="xlrd")
        except Exception as e:
            raise FileFormatError(f"Failed to read .xls file '{file_path}': {e}")

        # Step 2: Write to .xlsx
        try:
            df.to_excel(new_path, index=False)
        except Exception as e:
            raise FileFormatError(f"Failed to write .xlsx file '{new_path}': {e}")

        if log_conversion:
            self.logger.debug(f"Converted '{file_path}' → '{new_path}'.")

        return str(new_path)
