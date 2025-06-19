from myapp.utils.logger_config import get_logger
from typing import Any
import pandas as pd
from .base import FileFormatError
from .column_checker import ColumnChecker
from .date_checker import DateChecker
from .value_sanitizer import ValueSanitizer
from .xls_converter import XlsConverter


class FileValidator:
    def __init__(self) -> None:
        self.column_checker = ColumnChecker(
            {
                "job_id": ["job_id", "jobid"],
                "date": ["date"],
                "technician": ["technician", "tech"],
            }
        )
        self.date_checker = DateChecker("date")
        self.value_sanitizer = ValueSanitizer(["client", "technician"])
        self.xls_converter = XlsConverter()

    def validate(self, file_path: Any) -> pd.DataFrame:
        # Convert if needed
        actual_path = self.xls_converter.convert_to_xlsx(file_path)

        # Load the DataFrame
        try:
            df = pd.read_excel(actual_path)
        except Exception as e:
            raise FileFormatError(str(e))

        # Perform validations
        self.column_checker.check(df)
        self.date_checker.check(df)
        self.value_sanitizer.check(df)

        return df
