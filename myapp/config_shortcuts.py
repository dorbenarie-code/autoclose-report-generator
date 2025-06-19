# myapp/config_shortcuts.py

from myapp.config.settings import settings

# קיצורי דרך לנתיבים חשובים – עבור שימוש פשוט בקוד
UPLOAD_DIR    = settings.UPLOAD_FOLDER
EXPORT_DIR    = settings.CLIENT_REPORTS_FOLDER
MANIFEST_PATH = EXPORT_DIR / "manifest.json"
