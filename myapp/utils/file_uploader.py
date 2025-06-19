from myapp.utils.logger_config import get_logger
from typing import Optional

log = get_logger(__name__)
# utils/file_uploader.py

from pathlib import Path
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def save_uploaded_file(uploaded_file: FileStorage, upload_folder: Path) -> Path:
    """
    Saves the uploaded file securely to the target folder.
    Returns the full path of the saved file.
    """
    upload_folder.mkdir(parents=True, exist_ok=True)
    filename: Optional[str] = uploaded_file.filename
    if filename is None:
        raise ValueError("Missing file name")
    filename = secure_filename(filename)
    file_path = upload_folder / filename
    uploaded_file.save(file_path)
    return file_path
