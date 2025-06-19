import pandas as pd

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make sure 'tech' column exists by copying from known aliases if needed.
    """
    if "tech" not in df.columns or df["tech"].isna().all():
        for alias in ["technician", "tech_name"]:
            if alias in df.columns and not df[alias].isna().all():
                df["tech"] = df[alias]
                break
    return df
