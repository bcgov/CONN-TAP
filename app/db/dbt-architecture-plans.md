# dbt Architecture Plans — Telecom Reporting Pipeline

> **Project:** BC Gov Telecom Service Reporting Pipeline
> **Purpose:** Captures the dbt schema management discussion, including two alternative architecture proposals and operational additions.
> **Status:** Up for discussion — no plan finalised yet.

---

## Table of Contents

1. [Context](#1-context)
2. [Background: What dbt Is](#2-background-what-dbt-is)
3. [Plan A — Developer's 5-Layer Proposal](#3-plan-a--developers-5-layer-proposal)
4. [Plan B — Traditional 3-Layer dbt Proposal](#4-plan-b--traditional-3-layer-dbt-proposal)
5. [Plan Comparison](#5-plan-comparison)
6. [Operational Additions (Applies to Both Plans)](#6-operational-additions-applies-to-both-plans)
7. [Decision Framework](#7-decision-framework)

---

## 1. Context

The project pipeline transforms Excel files from Telus and Rogers into reporting data for entities like BC Gov, BCLC, ICBC, School Districts, and FNHA.

**Stack already decided:**
- Aurora PostgreSQL Serverless v2 (Athena dropped)
- AWS Glue + Step Functions for ETL
- FastAPI backend
- Next.js + Recharts frontend

**The data quality problem driving dbt adoption:**

Raw data from providers is messy. The same entity appears under multiple names across files:

```
"MOH"
"Ministry of Health"
"GOBC Min Health"
"Min Health"
"MoH - BC"
```

Without a structured transformation layer, queries devolve into fragile LIKE statements:

```sql
WHERE entity_name ILIKE '%health%'
   OR entity_name = 'MOH'
   OR entity_name = 'MoH - BC'
```

Both proposals below address this through canonical entity resolution — they differ in how many layers they use and how facts vs aggregates are separated.

---

## 2. Background: What dbt Is

**dbt = data build tool.** A CLI that runs SQL files from Git against PostgreSQL in dependency order, producing tables and views.

**Core concepts:**
- `.sql` files = models. Each one defines a table or view.
- `{{ ref('model_name') }}` = dependency between models. dbt builds the graph automatically.
- `{{ source('schema', 'table') }}` = reference to an external (non-dbt) table.
- `dbt run` = builds all models in order.
- `dbt test` = runs YAML-defined assertions on data.
- **Seeds** = CSV files in the repo loaded as tables. Version-controlled reference data.
- **Snapshots** = built-in versioning of model state over time.

**Key materialization types:**
- **View** — saved SQL, no data stored. Query runs live every time.
- **Materialized view (Postgres)** — pre-computed result stored on disk. Fast queries, refreshed on demand.
- **Table** — full snapshot stored. Rebuilt on every `dbt run`.

**Standard dbt layer convention (per dbt Labs):**

```
1. Staging       (stg_*)   — one model per source, atomic cleanup
2. Intermediate  (int_*)   — joins between staging, business logic, reusable
3. Marts         (mart_*)  — final business-ready tables for BI tools
```

**Important clarification:** "Traditional dbt" is three layers including Intermediate. Many simple projects skip Intermediate and go Staging → Marts, but that's a simplification, not the standard. Intermediate exists specifically to keep Staging atomic and Marts clean when joins and business logic are needed.

---

## 3. Plan A — Developer's 5-Layer Proposal

A more elaborate architecture that adds dedicated Reference and Core stages.

### Structure

```
Raw (text-only, raw_row_number from Excel)
    ↓
Staging (clean types, standardise names per source)
    ↓
Reference / Mapping (canonical entities + alias tables)
    ↓
Core (normalised factual records, uses IDs not names)
    ↓
Analytics (pre-computed aggregates for dashboards)
```

### Layer details

**Raw**
- Everything as `text` — never fails on type mismatch
- Includes `raw_row_number` from Excel for traceability
- Indestructible ingestion — garbage lands safely, gets handled downstream

**Staging**
- One model per provider/source (Telus, Rogers)
- Clean types, standardise column names
- Empty strings → null
- Phase 1 stopping point: ship materialized views on Staging, iterate the deeper layers later

**Reference / Mapping**
- Canonical dimension tables: `bge`, `providers`, `services`, `taxes`
- Alias tables: `bge_aliases`, `provider_aliases`, etc.
- Maps all real-world name variations to canonical IDs
- Future vision: UI for business users to manage mappings without developer involvement

**Core**
- Normalised factual tables: `factual_spend`, `factual_usage_quantity`
- All foreign keys reference Reference IDs — no string matching anywhere
- Versioning support for corrections (e.g. `is_current` flag, `superseded_by` reference)
- Answers "what happened?"

**Analytics**
- Pre-computed views and aggregates
- Dashboard-ready outputs
- FastAPI queries this layer only
- Answers "what does it mean?"

### Pros

- Full separation of concerns: facts (Core) vs aggregates (Analytics)
- Explicit support for corrections with audit history
- Reference layer makes alias management business-controlled
- Scales naturally as data complexity grows
- Strong fit for government auditability requirements

### Cons

- Five layers = more scaffolding, more files, slower Phase 1
- Custom pattern — onboarding overhead for anyone with standard dbt experience
- Reference as a database-managed layer requires more upfront work than seeds
- Risk of over-engineering for current data complexity

---

## 4. Plan B — Traditional 3-Layer dbt Proposal

Standard dbt structure used as intended, with BGE alias resolution handled inside Intermediate via dbt seeds.

### Structure

```
Raw (PostgreSQL — written by Glue, outside dbt)
    ↓
Staging (per-source cleanup + reference models from seeds)
    ↓
Intermediate (alias resolution, multi-source combination)
    ↓
Marts (aggregated, dashboard-ready)
```

### Layer details

**Staging**

Same as Plan A: one model per source, clean types, standardise names. Materialized as views.

Additional staging models reference dbt seeds:

```
models/staging/
  stg_telus_billing.sql
  stg_rogers_billing.sql
  stg_bge_canonical.sql       ← from seed
  stg_bge_aliases.sql         ← from seed
  stg_provider_aliases.sql    ← from seed
  stg_service_aliases.sql     ← from seed
```

**Reference data as dbt seeds**

Seeds = CSV files in the repo, loaded as tables via `dbt seed`. Version-controlled, PR-reviewed.

`seeds/bge_canonical.csv`:
```csv
bge_id,canonical_name,active
1,Ministry of Health,true
2,BCLC,true
3,ICBC,true
4,FNHA,true
5,School District 36,true
```

`seeds/bge_aliases.csv`:
```csv
bge_id,alias
1,MOH
1,Ministry of Health
1,GOBC Min Health
1,Min Health
1,MoH - BC
2,BCLC
2,British Columbia Lottery Corporation
3,ICBC
3,Insurance Corporation of BC
```

To update aliases: edit CSV → commit → PR → merge → `dbt seed` reloads. No DBA needed. When a management UI is built later, it writes to the same tables — seeds are a starting point, not a permanent constraint.

**Intermediate (the resolution layer)**

Three models do the work:

`int_billing_resolved_telus.sql`:
```sql
SELECT
    s.account_number,
    s.service_type,
    s.charge_amount,
    s.billing_date,
    'telus'                       as provider,
    coalesce(b.bge_id, -1)        as bge_id,
    s.entity_name_raw             as original_entity_name
FROM {{ ref('stg_telus_billing') }} s
LEFT JOIN {{ ref('stg_bge_aliases') }} a
    ON lower(trim(s.entity_name_raw)) = lower(trim(a.alias))
LEFT JOIN {{ ref('stg_bge_canonical') }} b
    ON a.bge_id = b.bge_id
```

`int_billing_resolved_rogers.sql` — same pattern.

`int_billing_combined.sql`:
```sql
SELECT * FROM {{ ref('int_billing_resolved_telus') }}
UNION ALL
SELECT * FROM {{ ref('int_billing_resolved_rogers') }}
```

Result: a single combined billing table with canonical entity IDs. No LIKE statements anywhere downstream. This intermediate model functions as the de facto fact table — just without the explicit "Core" naming.

**Marts**

Aggregated, materialized, refreshed per pipeline run.

```sql
-- mart_entity_monthly_spend.sql
SELECT
    b.canonical_name      as entity_name,
    i.provider,
    date_trunc('month', i.billing_date) as billing_month,
    sum(i.charge_amount)  as total_charges,
    count(*)              as line_item_count
FROM {{ ref('int_billing_combined') }} i
LEFT JOIN {{ ref('stg_bge_canonical') }} b
    ON i.bge_id = b.bge_id
WHERE i.bge_id != -1
GROUP BY 1, 2, 3
```

### Critical tests

```yaml
models:
  - name: int_billing_combined
    tests:
      - dbt_utils.expression_is_true:
          expression: "bge_id != -1"
          severity: error      # fails pipeline on unmatched entities
      - dbt_utils.row_count_equal:
          compare_model: ref('stg_billing_all')
          severity: error      # no rows lost in resolution
    columns:
      - name: bge_id
        tests:
          - not_null
          - relationships:
              to: ref('stg_bge_canonical')
              field: bge_id
      - name: charge_amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "charge_amount >= 0"
```

The unmatched-entity test makes this design safe: pipeline stops if a new alias appears that isn't mapped. Someone adds it to the CSV, opens a PR, merges, re-runs. Bad data never reaches Marts.

### Corrections approach

No versioned Core layer means corrections work differently:

1. New corrected file lands in S3
2. Glue replaces raw rows for the affected period (delete-then-insert by `period + provider`)
3. dbt re-runs — staging, intermediate, marts all rebuild
4. Materialized views refresh with corrected data

**Trade-off:** loses point-in-time audit ("what did the April 5th report show?"). Mitigated by a lightweight audit table outside dbt:

```sql
audit_load_history:
┌─────────┬──────────┬──────────┬──────────────┬────────────┬───────────┐
│ load_id │ provider │ period   │ uploaded_at  │ row_count  │ file_hash │
└─────────┴──────────┴──────────┴──────────────┴────────────┴───────────┘
```

### Folder structure

```
dbt/
├── dbt_project.yml
├── profiles.yml
├── seeds/
│   ├── bge_canonical.csv
│   ├── bge_aliases.csv
│   ├── providers_canonical.csv
│   ├── providers_aliases.csv
│   ├── services_canonical.csv
│   └── services_aliases.csv
├── models/
│   ├── staging/
│   │   ├── sources.yml
│   │   ├── schema.yml
│   │   ├── stg_telus_billing.sql
│   │   ├── stg_rogers_billing.sql
│   │   ├── stg_bge_canonical.sql
│   │   ├── stg_bge_aliases.sql
│   │   ├── stg_provider_aliases.sql
│   │   └── stg_service_aliases.sql
│   ├── intermediate/
│   │   ├── schema.yml
│   │   ├── int_billing_resolved_telus.sql
│   │   ├── int_billing_resolved_rogers.sql
│   │   └── int_billing_combined.sql
│   └── marts/
│       ├── schema.yml
│       ├── mart_entity_monthly_spend.sql
│       ├── mart_provider_split.sql
│       └── mart_executive_summary.sql
├── tests/
│   └── singular/
│       └── assert_no_unmatched_entities.sql
└── macros/
```

### Pros

- Canonical dbt structure — anyone with dbt experience reads it and knows where to look
- Faster Phase 1 delivery — three layers, less scaffolding
- Seeds are version-controlled and PR-reviewable — clean audit trail of alias changes
- Lower onboarding cost for new developers
- Avoids over-engineering — complexity added only when justified

### Cons

- Corrections lose history (no built-in versioning)
- No clean fact/aggregate separation — Intermediate doubles as fact table
- Seeds have practical size limits (hundreds of rows, not thousands)
- Less room to evolve into SCD Type 2, cost allocation, or point-in-time queries without refactor
- Intermediate models can become dense if business rules grow

---

## 5. Plan Comparison

| Aspect | Plan A — 5-layer | Plan B — 3-layer (traditional) |
|--------|------------------|--------------------------------|
| Number of layers | 5 (Raw, Staging, Reference, Core, Analytics) | 3 (Staging, Intermediate, Marts) — standard dbt |
| BGE alias resolution | Dedicated Reference stage | Inside Intermediate via seed-based joins |
| Reference data storage | Database tables, future UI | dbt seeds (CSV in Git) initially |
| Fact vs aggregate separation | Explicit (Core vs Analytics) | Combined in Marts |
| Correction handling | Versioning with `is_current` flag | Re-run pipeline for period |
| Audit trail | Built into Core records | Separate audit table outside dbt |
| Conformance to dbt convention | Custom extension | Standard dbt pattern |
| Complexity | Higher | Lower |
| Time to ship Phase 1 | Longer | Shorter |
| Future flexibility | More room to evolve | Refactor needed for growth |
| Government auditability | Strong | Workable with audit table |

### When to choose which

| Choose Plan B (3-layer) if... | Choose Plan A (5-layer) if... |
|-------------------------------|-------------------------------|
| Team is new to dbt and standard patterns matter | Team has dbt experience |
| Phase 1 needs to ship in 6 weeks | Timeline allows for architecture upfront |
| Correction audit trail isn't a hard requirement | Government auditability requires point-in-time queries |
| Reference data fits in CSV files | Reference data is large or needs UI immediately |
| Reporting requirements are stable | Reporting needs expected to grow significantly |
| Operational simplicity > future-proofing | Long-term flexibility > time-to-ship |

---

## 6. Operational Additions (Applies to Both Plans)

These additions apply regardless of which structural plan is chosen.

### 6.1 Pipeline audit tables

Neither plan tracks data movement explicitly. Add:

```
pipeline_runs:
┌────────────┬──────────┬──────────────┬──────────┬─────────────┬────────┬───────────┐
│ run_id     │ provider │ report_type  │ period   │ uploaded_at │ status │ row_count │
└────────────┴──────────┴──────────────┴──────────┴─────────────┴────────┴───────────┘

upload_audit:
┌──────────┬──────────┬────────────┬──────────────┬──────────────┬───────────┐
│ audit_id │ run_id   │ uploaded_by│ source_file  │ s3_path      │ file_hash │
└──────────┴──────────┴────────────┴──────────────┴──────────────┴───────────┘
```

Answers: "When was this data loaded? By whom? Did it pass tests? What was the row count?"

Required for government audit trail.

### 6.2 Explicit dbt test taxonomy

Both plans need a defined test suite. Required categories:

- **Schema tests** — column presence, types, nullability (dbt built-ins)
- **Referential tests** — every staging alias maps to a canonical ID
- **Volume tests** — row count within expected range for the period (catches truncated files)
- **Business rule tests** — non-negative charges, billing dates within period
- **Anomaly tests** — current period deviates >X% from rolling average (catches format errors, transposed digits)

The volume sanity test is the standout — catches the silent disaster of a half-loaded file that parses cleanly:

```yaml
- dbt_utils.row_count:
    above: 4500
    below: 5500
```

### 6.3 Period dimension

BC government fiscal year runs April–March. Without an explicit period dimension every analyst writes their own fiscal logic and gets it wrong. Add:

```
dim_period:
┌──────────┬──────┬───────┬─────────┬─────────────┬────────────────┐
│ period_id│ year │ month │ quarter │ fiscal_year │ fiscal_quarter │
│ 2025-01  │ 2025 │ 1     │ Q1      │ 2024-25     │ Q4             │
└──────────┴──────┴───────┴─────────┴─────────────┴────────────────┘
```

Every report joins `dim_period` and gets consistent fiscal handling.

### 6.4 SCD Type 2 on Reference dimensions

Entities reorganise and rename over time:
- Ministry of Health → Ministry of Health and Wellness
- School districts split
- BCLC reorganisations

Add effective/end dates to canonical tables:

```
bge:
┌────────┬─────────────────────────┬────────────┬────────────┬────────────┐
│ bge_id │ canonical_name          │ effective  │ end_date   │ is_current │
│ 1      │ Ministry of Health      │ 2020-01-01 │ 2024-06-30 │ false      │
│ 1      │ Ministry of Health      │ 2024-07-01 │ null       │ true       │
│        │ and Wellness            │            │            │            │
└────────┴─────────────────────────┴────────────┴────────────┴────────────┘
```

January 2024 report shows old name. July 2024 report shows new name. Both correct for their context.

### 6.5 Snapshot strategy for published reports

For reports presented to leadership that may be referenced months later:

**Option A — dbt snapshots:** built-in versioning of every row over time.

**Option B — Point-in-time materialized tables:** freeze `mart_*_q1_2025_published_2025_04_01` at moment of publication. Never updated.

For government context, Option B is safer — can always reconstruct exactly what was reported at a given time.

### 6.6 Failure mode runbook

Document explicitly what happens when things go wrong:

| Failure | Detection | Response | Recovery |
|---------|-----------|----------|----------|
| Provider file doesn't arrive by deadline | Scheduled check Lambda | SNS alert to ops | Manual follow-up with provider |
| File arrives but fails schema validation | Glue validation step | Step Functions failure → SNS | Provider resubmits |
| File passes schema but fails dbt tests | dbt test step | Pipeline stops, dashboard serves last good data | Investigate, manually flag, re-run |
| Unmatched alias in new file | dbt relationships test | Pipeline stops | Add alias to CSV/table, re-run |
| Materialized view refresh fails | dbt run failure | Dashboard shows stale + warning banner | Manual refresh, root cause investigation |

Teams that don't write this end up improvising the response during the first real failure.

### 6.7 Cross-provider reconciliation tests

Domain-specific tests for telecom billing:

- Same entity reported by Telus vs Rogers under different aliases (caught by reference resolution)
- Entity active last period but missing this period (potential dropped data)
- Unexpected new entities in one provider's file but not the other

```yaml
- entity_continuity:
    threshold_drop_percent: 50
    excluded_entities: ref('dim_entity_offboarded')
```

### 6.8 Phasing — make boundaries explicit

Without phases, teams build the perfect architecture for six months and ship nothing.

**Phase 1 — Ship working dashboards (Weeks 1–6):**
- Raw + Staging layers
- Materialized views directly on staging for top 5 dashboards
- Basic dbt tests (not_null, unique, accepted_values)

**Phase 2 — Reference & resolution (Weeks 7–14):**
- Reference data populated (seeds or tables)
- Aliases populated by walking historical data
- Intermediate / Core layer with proper resolution
- Dashboards migrated to query resolved data
- Unmatched alias test enforced

**Phase 3 — Operational maturity (Weeks 15+):**
- Pipeline audit tables
- SCD Type 2 on dimensions
- Period dimension
- Anomaly detection tests
- Reference management UI

### 6.9 Cost allocation placeholder

Forward-looking note: telecom billing involves cost allocation (Ministry of Health pays for school district services billed through BC Gov). Don't build it now, but design Core/Intermediate with allocation in mind so adding it later doesn't require schema rewrites.

```
core.factual_spend         ← what was billed
allocation.allocated_spend  ← who actually owes after rules (future)
analytics.mart_*            ← reports based on allocated, not billed
```

---

## 7. Decision Framework

Both plans solve the BGE name problem. Both are defensible. The decision should be based on:

1. **Timeline pressure** — Plan B ships Phase 1 sooner
2. **Team dbt experience** — Plan B easier for newcomers; Plan A requires more dbt fluency
3. **Audit requirements** — Plan A handles point-in-time auditability natively; Plan B needs additional audit tables
4. **Future complexity** — Plan A scales better to cost allocation, multi-period corrections, complex versioning
5. **Reference data scale** — Plan B's seeds work for hundreds of rows; Plan A's tables handle thousands and a future UI

### Recommended approach

Regardless of plan chosen, adopt the **operational additions in Section 6**. They're not architecture choices — they're production-readiness requirements for a government context.

For Plan B specifically: design the Intermediate models so that splitting Intermediate into Core+Analytics later (if needed) is a refactor, not a rewrite. Use ID-keyed joins everywhere from day one. This preserves the option to evolve into Plan A's structure if requirements grow.

---

## Appendix: Quick Reference

### Standard dbt commands

```bash
dbt seed              # Load CSV seeds into the database
dbt run               # Build all models in dependency order
dbt test              # Run all tests
dbt run && dbt test   # Full pipeline (what runs in Step Functions)
dbt docs generate     # Build documentation site
dbt docs serve        # Serve docs locally
```

### Materialization decision rule

| Layer | Materialization | Why |
|-------|----------------|-----|
| Staging | View | Cheap, always fresh, just type casting |
| Intermediate | View or ephemeral | Internal, reused by marts |
| Marts | Materialized view or table | Fast queries, expensive aggregations |

### Layer naming conventions

```
stg_<source>_<entity>     — staging
int_<entity>_<verb>       — intermediate (e.g. int_billing_resolved)
mart_<audience>_<metric>  — marts (e.g. mart_executive_summary)
fct_<entity>              — fact tables (if using dimensional modelling)
dim_<entity>              — dimension tables
```

---

*This document captures the dbt architecture discussion from the project planning phase. It is intended as a starting point for further refinement once Phase 1 scope is locked in.*
