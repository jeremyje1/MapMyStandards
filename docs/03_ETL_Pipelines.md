# 03 – ETL & data contracts

| Source | Airbyte connector | Incremental key | Notes |
|--------|------------------|-----------------|-------|
| Canvas LMS | `source-canvas` | `updated_at` | Requires Canvas API key scope: *courses:read* |
| Banner SIS | `jdbc-postgres` | `updated_at` | On‑prem JDBC tunnel via SSH bastion |
| SharePoint | `source-sharepoint` | `modified` | Uses Microsoft Graph OAuth 2 |

All connectors write to a **Lakehouse Bronze** schema (`raw_*` tables).  
A **dbt** job models that into **Silver** tables used by the Mapper agent.

```bash
airbyte run connection canvas_conn
dbt run --select evidence_dimension
```
