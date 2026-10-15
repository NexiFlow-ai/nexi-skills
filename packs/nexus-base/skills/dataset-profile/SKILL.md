# Dataset profile

You write the **ingest cell**: pandas code that reads the attached file, keeps a Parquet copy for later stages and profiles every field.

- The cell starts with `import nexus` and `import pandas as pd` — `nexus` is the sandbox's module (`nexus.metric · table · chart · text · file`), not a built-in.
- Read with pandas: `.xlsx` → `pd.read_excel(path, sheet_name="<data sheet>", engine="openpyxl")` where the data sheet is the one the source hint names (`sheet “…”`, the sheet with the most rows); `.csv/.tsv` → `pd.read_csv`; `.parquet` → `pd.read_parquet`; `.json` → `pd.read_json`. The file is at `/nexus/in/<filename>`.
- A two-column sheet whose first column matches data column names is a **definitions** sheet — read it separately, keep it as a table (`Field definitions`) and use it to name things; never profile it as the data.
- Save the data frame as `dataset.parquet`: coerce **every** `object` column first — `obj = df.select_dtypes(include="object").columns; df[obj] = df[obj].astype("string")` (Arrow refuses a column that mixes dates, numbers and text, and a `datetime64` check does not see them) — then `df.to_parquet("dataset.parquet", index=False)` and `nexus.file("dataset.parquet", "dataset.parquet")`.
- Profile per field with a generic loop — pandas has no `df.profile()`:

  ```python
  rows = []
  for c in df.columns:
      col = df[c]
      parsed = pd.to_datetime(col, errors="coerce") if col.dtype == object else None
      kind = ("datetime" if parsed is not None and parsed.notna().mean() > 0.8
              else "number" if pd.api.types.is_numeric_dtype(col)
              else "boolean" if pd.api.types.is_bool_dtype(col)
              else "id" if col.nunique() == len(col.dropna()) > 0
              else "category" if col.nunique() <= 50 else "text")
      samples = " | ".join(str(v)[:40] for v in col.dropna().unique()[:3])
      rows.append({"field": str(c), "type": kind, "missing_pct": round(col.isna().mean() * 100, 1),
                   "distinct": int(col.nunique()), "samples": samples})
  profile = pd.DataFrame(rows)
  nexus.table(profile, "Dataset profile")
  ```

  Emit it **data first, title second**; up to **three** sample values, each shortened to 40 chars.
- Metrics are single numbers: `nexus.metric("rows", len(df))`, `nexus.metric("columns", df.shape[1])`, `nexus.metric("sheets", n)`, and last `nexus.metric("profile.completed", 1)`. Add `dq.critical_errors` = number of fields that are entirely empty or duplicate another field's values. Never pass a tuple (`df.shape`) or a string as a value.
- Output exactly `{code, intent}`; `intent` is one sentence of what the cell does. No rows, no cell values in `intent`.
