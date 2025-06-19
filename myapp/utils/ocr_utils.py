from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
# utils/ocr_utils.py

import logging
from pathlib import Path

from PIL import Image, UnidentifiedImageError
import pytesseract
from myapp.utils.logger_config import get_logger

logger = get_logger(__name__)


class OCRProcessor:
    """
    OCR engine for extracting text from image files.
    Includes fallback handling and logging for robustness.
    """

    def _load_image(self, image_path: str) -> Image.Image:
        """
        Safely load an image from the given path.

        Raises:
            FileNotFoundError: If the file does not exist.
            UnidentifiedImageError: If PIL cannot identify the image format.
        """
        path = Path(image_path)
        if not path.is_file():
            logger.error(f"File not found: {image_path}")
            raise FileNotFoundError(image_path)

        try:
            logger.info(f"Opening image: {image_path}")
            return Image.open(path)
        except UnidentifiedImageError:
            logger.error(f"Unsupported image format: {image_path}")
            raise

    def _perform_ocr(self, image: Image.Image, lang: str = "eng") -> str:
        """
        Perform OCR on the image and return cleaned text.

        Returns:
            The extracted text, stripped of leading/trailing whitespace.
            Returns an empty string on failure.
        """
        try:
            logger.info(f"Running OCR (lang={lang})...")
            raw_text = pytesseract.image_to_string(image, lang=lang)
            result = raw_text.strip()
            logger.info(f"OCR succeeded ({len(result)} chars)")
            return result
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def extract_text_from_path(self, image_path: str, lang: str = "eng") -> str:
        """
        Public method to load an image and return OCR text.

        Returns:
            The extracted text, or an empty string if an error occurs.
        """
        try:
            image = self._load_image(image_path)
            return self._perform_ocr(image, lang=lang)
        except (FileNotFoundError, UnidentifiedImageError) as e:
            logger.warning(f"OCR skipped due to error: {e}")
            return ""
        except Exception as e:
            logger.warning(f"Unexpected error during OCR: {e}")
            return ""
