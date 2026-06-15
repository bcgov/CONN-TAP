# Telus classification exploration queries

SQL used to analyze pricebook-based classification for `raw_data.raw_telus_spend`.
See internal telus_classification.md for findings and recommendations.

Run against Postgres with `raw_data` schema populated (spend + pricebooks ingested).

```bash
cd scripts/validation/telus/classification
psql "$DATABASE_URL" -f 01_pricebook_inventory.sql
```

## Files

| File | Purpose |
|------|---------|
| [`_common.sql`](./_common.sql) | Shared normalization helpers and spend filter (reference only) |
| [`01_pricebook_inventory.sql`](./01_pricebook_inventory.sql) | Pricebook table row counts and sample entries |
| [`02_source_id_distribution.sql`](./02_source_id_distribution.sql) | `source` / `source_id` distribution in spend |
| [`03_data_ng_prefix_match_rate.sql`](./03_data_ng_prefix_match_rate.sql) | Data bucket: NG-prefix match rate and methods |
| [`04_voice_recurring_match_rate.sql`](./04_voice_recurring_match_rate.sql) | Voice recurring: NG / text match breakdown |
| [`05_voice_to_data_misclassifications.sql`](./05_voice_to_data_misclassifications.sql) | Voice `source_id` rows that match data pricebook |
| [`06_wireline_pb_vs_source_id.sql`](./06_wireline_pb_vs_source_id.sql) | Wireline NG-code pricebook vs `source_id` bucket |
| [`07_wireless_gobc_mapping_coverage.sql`](./07_wireless_gobc_mapping_coverage.sql) | Cellular: GoBC plan name → pricebook `service_id` |
| [`08_data_non_ng_rows.sql`](./08_data_non_ng_rows.sql) | Data rows without `NG#####` prefix |
| [`09_voice_unmatched_recurring.sql`](./09_voice_unmatched_recurring.sql) | Top unmatched voice recurring by amount |
| [`10_fuzzy_pricebook_match_caution.sql`](./10_fuzzy_pricebook_match_caution.sql) | **Slow** — broad fuzzy matcher (illustrates cellular false positives) |
| [`11_partial_text_match_caution.sql`](./11_partial_text_match_caution.sql) | **Slow** — flawed `POSITION` partial text match |
| [`12_proposed_vs_current_bucket_caution.sql`](./12_proposed_vs_current_bucket_caution.sql) | **Very slow** — full proposed logic incl. partial text (do not use $ figures) |

Queries marked **Slow** / **Very slow** scan most of `raw_telus_spend` (~11M rows). Prefer 01–09 for routine analysis.

**Slow** queries performed in less than 1 hour

**Very slow** query took more than 1 hour
