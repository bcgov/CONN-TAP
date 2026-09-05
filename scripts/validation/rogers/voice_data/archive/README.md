# Archived — legacy Python/Excel validation (data/voice)

These scripts are the **retired** file-based validation path. They read a monthly Rogers
data/voice Excel export and wrote an Excel report with one sheet per check, using **hardcoded**
mappings in `mapping.py`.

They have been **replaced** by the SQL/database path in the parent folder:

- `../checks/*.sql` — a view + one Postgres function per check, using
  the DB **seeds/reference data** (`seeds.bge_alias_map`, `seeds.sub_bge_alias_map`,
  `reference_data.bge/sub_bge`) as the source of truth, and the shared `norm_key` matching.
- `../run_validations.py` — connects to Postgres, runs each function, and writes the same
  per-check Excel workbook (plus a Summary tab, month-over-month detection, and, with
  `--month`, a Spend Comparison).

Kept for reference only — nothing active imports these. They are not wired into any runner.
Do not use them for new validation runs; use `../run_validations.py` instead.
