import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List
import pandas as pd
import os
import logging

from myapp.utils.logger_config import get_logger
from myapp.config_shortcuts import MANIFEST_PATH
from myapp.utils.decimal_utils import apply_safe_decimal
from decimal import Decimal

log = logging.getLogger(__name__)


def get_total(df) -> float:
    """
    Compute the total value of the report from a DataFrame.
    Expects a DataFrame with a 'total' column and returns its sum.
    """
    from pandas import DataFrame

    if not isinstance(df, DataFrame):
        raise TypeError(f"get_total expected DataFrame, got {type(df).__name__}")

    if "total" not in df.columns:
        raise ValueError("Missing 'total' column in DataFrame")

    # Exclude any Totals row (where job_id starts with "Totals")
    df_sum = df
    if "job_id" in df.columns:
        mask = ~df["job_id"].astype(str).str.startswith("Totals")
        df_sum = df[mask]
    return df_sum["total"].sum()


def add_report_to_manifest(
    *,
    df: pd.DataFrame,
    report_path: str,
    report_type: str,
    client_id: str,
    tech_name: str
) -> None:
    log.debug(f"[TYPECHECK] {__name__}.add_report_to_manifest → got {type(df).__name__} with shape {getattr(df, 'shape', 'N/A')}")
    # 1. load manifest
    manifest = []
    if os.path.isfile(MANIFEST_PATH) and os.path.getsize(MANIFEST_PATH) > 0:
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            try:
                manifest = json.load(f)
            except json.JSONDecodeError:
                raise ValueError("Malformed manifest.json")
        if not isinstance(manifest, list):
            raise ValueError("Malformed manifest.json")

    # 2. validate report_path
    if not isinstance(report_path, Path):
        raise ValueError(f"report_path must be a pathlib.Path, got {type(report_path).__name__}")

    # 3. skip duplicates
    report_path_str = str(report_path)
    if any(entry.get("path") == report_path_str for entry in manifest):
        log.info("Manifest already contains entry for path %s, skipping", report_path_str)
        return pd.DataFrame(manifest).shape

    log.info("🚀 Starting add_report_to_manifest stage")
    try:
        from pandas import DataFrame
        func_name = "add_report_to_manifest"
        if not isinstance(df, DataFrame):
            log.debug("TYPECHECK: %s in %s", type(df).__name__, func_name)
            raise TypeError(f"{func_name} expected DataFrame, got {type(df).__name__}")
        log.debug("TYPECHECK: %s in %s", type(df).__name__, func_name)
        if isinstance(df, pd.Series):
            raise TypeError("\u274c df צריך להיות DataFrame – קיבלת Series בטעות!")
        # 💣 הגנה: לוודא df הוא באמת DataFrame
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"❌ add_report_to_manifest: expected DataFrame, got {type(df)}")

        # בדיקה מפורשת ל-DataFrame ריק
        if df.empty:
            raise ValueError("DataFrame is empty")

        # 🧪 בדיקה שהעמודות הקריטיות קיימות
        required_cols = {"job_id", "total"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"❌ Missing columns in df: {missing_cols}")

        # בדיקת טיפוס ל-report_path
        if not isinstance(report_path, Path):
            raise ValueError(f"add_report_to_manifest: report_path must be pathlib.Path, got {type(report_path).__name__}")

        # timestamp ב־UTC ISO8601 עם סיומת Z
        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # ספירת שורות נתונים בלבד (ללא שורת Totals אם קיימת)
        rows_count = len(df)
        if "job_id" in df.columns:
            rows_count = int((~df["job_id"].astype(str).str.startswith("Totals")).sum())

        # סכימת total על שורות הנתונים בלבד
        total_amount = get_total(df)

        # בנה את הרשומה החדשה
        manifest_entry = {
            "created_at": created_at,
            "updated_at": created_at,  # אופציונלי
            "filename": os.path.basename(report_path),
            "path": str(report_path),
            "rows": rows_count,
            "total": float(total_amount),
            "client_id": client_id,
            "tech_name": tech_name,
            "report_type": report_type,
        }
        # Integrate validation status if present
        validation = getattr(df, "_autoclose_validation", None)
        if validation:
            manifest_entry["validated"] = validation.get("validated")
            manifest_entry["validation_notes"] = validation.get("validation_notes")

        manifest.append(manifest_entry)

        # שמור בחזרה
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, default=str, ensure_ascii=False, indent=2)
        # return shape
        manifest_df = pd.DataFrame(manifest)
        log.info("✅ add_report_to_manifest complete → total records %d", len(manifest))
        return manifest_df.shape
    except Exception as e:
        log.exception(f"[ERROR] Failed inside add_report_to_manifest – {e}")
        log.debug(f"[DF] Columns: {getattr(df, 'columns', [])}")
        log.debug(f"[DF] Head:\n{getattr(df, 'head', lambda x=3: 'N/A')(3)}")
        raise


def load_manifest_as_list() -> List[Dict]:
    """
    Load the JSON manifest and return it as a list of dicts.
    If the file is missing or malformed, return an empty list.
    """
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # אם השתמר כמבנה אחר (dict), נסו לחלץ את המפתח המתאים
            if isinstance(data, list):
                return data
            return data.get("reports", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []
