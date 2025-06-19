from myapp.utils.logger_config import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Base class for all validation errors."""

    pass


class FileFormatError(ValidationError):
    def __init__(
        self, message: str = "Unsupported file format. Only .xlsx files are allowed."
    ) -> None:
        super().__init__(message)


class MissingColumnError(ValidationError):
    def __init__(self, column: str) -> None:
        super().__init__(f"Missing required column: '{column}'")


class InvalidDateError(ValidationError):
    def __init__(self, value: str) -> None:
        super().__init__(f"Invalid date value: '{value}'")


class DataSanitizationError(ValidationError):
    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"Invalid character in field '{field}': '{value}'")
