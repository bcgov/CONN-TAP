# Data Pipeline Architecture

```mermaid
flowchart TD
    subgraph Sources["Data Sources"]
        S3_TSMA["S3: TSMA Excel Files\nData_Voice.xlsx / Cellular.xlsx"]
        S3_TELUS["S3: Telus Spend Reports"]
        S3_ROGERS["S3: Rogers Spend Reports"]
    end

    subgraph Ingestion["Ingestion Layer (AWS)"]
        LAMBDA["Lambda Trigger"]
        GLUE_TSMA["Glue: tsma_qsr_ingestion.py"]
        GLUE_TELUS["Glue: telus_spend_ingestion.py"]
        GLUE_ROGERS["Glue: rogers_spend_ingestion.py"]
    end

    subgraph RawDB["raw_data schema (Postgres)"]
        RAW_TSMA_W["tsma_wireless\ntsma_lite_wireless"]
        RAW_TSMA_WL["tsma_wireline\ntsma_lite_wireline"]
        RAW_TSMA_IVR["tsma_ivr\ntsma_mms"]
        RAW_TSMA_OTHER["tsma_other_managed_security\ntsma_other_managed_router"]
        RAW_TELUS["raw_telus_spend\ntelus_quantities"]
        RAW_ROGERS["raw_rogers_spend_cellular\nraw_rogers_spend_data_voice"]
        RUN_TSMA["tsma_ingestion_run"]
        RUN_NGTA["ngta ingestion_run"]
    end

    subgraph DBT_STAGING["dbt: staging/ (SQL Views)"]
        STG_TSMA_W["stg_tsma_wireless\n• normalize BGE names\n• cast ccyymm → date\n• map service towers"]
        STG_TSMA_WL["stg_tsma_wireline\n• normalize BGE names\n• map service towers"]
        STG_TSMA_IVR["stg_tsma_ivr_mms\n• combine IVR + MMS"]
        STG_TELUS["stg_ngta_telus\n• unified NGTA structure\n• map categories"]
        STG_ROGERS["stg_ngta_rogers\n• unified NGTA structure\n• map categories"]
    end

    subgraph RefDB["reference_data schema (Postgres)"]
        REF_BGE["bge_aliases\n(raw_name → canonical_name)"]
        REF_CAT["service_categories\n(raw_category → display_name, tower)"]
    end

    subgraph DBT_MARTS["dbt: marts/ (Materialized Tables)"]
        MART_TSMA["tsma_monthly_spend\n(bge, period, service_tower,\ncategory, billed_amt)"]
        MART_NGTA["ngta_monthly_spend\n(bge, period, provider,\ncategory, billed_amt)"]
    end

    subgraph API["FastAPI Backend"]
        DS_TSMA["datasets/tsma_spend/\nservice.py + queries.sql"]
        DS_NGTA["datasets/ngta_spend/\nservice.py + queries.sql"]
        REGISTRY["datasets/registry.py\n(auto-discovery)"]
    end

    subgraph Frontend["Next.js Frontend"]
        DASHBOARD["Dashboard /datasets"]
    end

    %% Ingestion flow
    S3_TSMA --> LAMBDA --> GLUE_TSMA
    S3_TELUS --> LAMBDA --> GLUE_TELUS
    S3_ROGERS --> LAMBDA --> GLUE_ROGERS

    GLUE_TSMA --> RAW_TSMA_W & RAW_TSMA_WL & RAW_TSMA_IVR & RAW_TSMA_OTHER & RUN_TSMA
    GLUE_TELUS --> RAW_TELUS & RUN_NGTA
    GLUE_ROGERS --> RAW_ROGERS & RUN_NGTA

    %% Staging flow
    RAW_TSMA_W --> STG_TSMA_W
    RAW_TSMA_WL --> STG_TSMA_WL
    RAW_TSMA_IVR --> STG_TSMA_IVR
    RAW_TELUS --> STG_TELUS
    RAW_ROGERS --> STG_ROGERS

    REF_BGE -.->|alias lookup| STG_TSMA_W & STG_TSMA_WL
    REF_CAT -.->|category mapping| STG_TELUS & STG_ROGERS

    %% Marts flow
    STG_TSMA_W & STG_TSMA_WL & STG_TSMA_IVR --> MART_TSMA
    STG_TELUS & STG_ROGERS --> MART_NGTA

    %% API flow
    MART_TSMA --> DS_TSMA
    MART_NGTA --> DS_NGTA
    DS_TSMA & DS_NGTA --> REGISTRY --> DASHBOARD

    %% Styling
    classDef raw fill:#f5c542,stroke:#c49a00,color:#000
    classDef staging fill:#74b9ff,stroke:#0984e3,color:#000
    classDef marts fill:#55efc4,stroke:#00b894,color:#000
    classDef ref fill:#fd79a8,stroke:#e84393,color:#000
    classDef api fill:#a29bfe,stroke:#6c5ce7,color:#000

    class RAW_TSMA_W,RAW_TSMA_WL,RAW_TSMA_IVR,RAW_TSMA_OTHER,RAW_TELUS,RAW_ROGERS,RUN_TSMA,RUN_NGTA raw
    class STG_TSMA_W,STG_TSMA_WL,STG_TSMA_IVR,STG_TELUS,STG_ROGERS staging
    class MART_TSMA,MART_NGTA marts
    class REF_BGE,REF_CAT ref
    class DS_TSMA,DS_NGTA,REGISTRY api
```

## Layer Summary

| Layer | Schema / Location | Materialization | Purpose |
|-------|------------------|-----------------|---------|
| **Raw** | `raw_data.*` | Tables | Historical archive, as-received from provider |
| **Staging** | `dbt: staging/` | Views | Normalize, cast, alias — no aggregation |
| **Reference** | `reference_data.*` | Tables (migrations) | Lookup data (BGE aliases, category maps) — editable without deploy |
| **Marts (Clean)** | `dbt: marts/` | Tables | Reporting-ready, aggregated by BGE/period/category |
| **Dataset plugins** | `app/backend/app/datasets/` | — | FastAPI layer over marts |

## Key Decoupling Principle

Ingestion scripts (Glue jobs) write only to `raw_data` — they have no knowledge of reporting structure.
dbt models read only from `raw_data` sources — they have no knowledge of how data arrived.
