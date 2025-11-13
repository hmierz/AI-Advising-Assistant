# app/rules.py
import pandas as pd
from pathlib import Path

RULES_VERSION = "0.0-minimal"

BASE = Path(__file__).parent

def check_requirements(df: pd.DataFrame, program: str, catalog_year: str) -> dict:
    """
    Minimal checks so the app runs:
      - verifies Category and Credits columns exist
      - verifies Credits are numeric
      - warns if total credits < 12
    """
    issues = []

    # column names (case-insensitive)
    cols = {c.lower(): c for c in df.columns}
    cat_col = cols.get("category")
    cr_col  = cols.get("credits")

    if not cat_col:
        issues.append({"type": "Missing column", "course": "(n/a)", "details": "CSV missing 'Category' column"})
    if not cr_col:
        issues.append({"type": "Missing column", "course": "(n/a)", "details": "CSV missing 'Credits' column"})

    if cat_col and cr_col:
        # numeric check
        numeric = pd.to_numeric(df[cr_col], errors="coerce")
        bad_rows = df[numeric.isna()]
        for i, row in bad_rows.iterrows():
            issues.append({
                "type": "Bad credits",
                "course": str(row.get("Course", f"row {i+1}")),
                "details": f"Credits '{row[cr_col]}' is not numeric"
            })

        total = numeric.fillna(0).sum()
        if total < 12:
            issues.append({"type": "Low load", "course": "(overall)", "details": f"Total credits {total:.1f} < 12"})

    return {"issues": issues, "summary": {"program": program, "catalog_year": catalog_year}}
