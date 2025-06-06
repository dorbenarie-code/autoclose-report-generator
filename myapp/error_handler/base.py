class ValidationError(Exception):
    """Base class for all validation errors."""

    pass


class FileFormatError(ValidationError):
    def __init__(
        self, message="Unsupported file format. Only .xlsx files are allowed."
    ):
        super().__init__(message)


class MissingColumnError(ValidationError):
    def __init__(self, column):
        super().__init__(f"Missing required column: '{column}'")


class InvalidDateError(ValidationError):
    def __init__(self, value):
        super().__init__(f"Invalid date value: '{value}'")


class DataSanitizationError(ValidationError):
    def __init__(self, field, value):
        super().__init__(f"Invalid character in field '{field}': '{value}'")
