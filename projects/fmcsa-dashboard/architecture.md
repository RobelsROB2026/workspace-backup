# FMCSA Dashboard Architecture

## 1. Modular Directory Structure
```
fmcsa-dashboard/
├── data-pipeline/     # Python ETL scripts for daily FMCSA data pulling
├── api/               # Express/Node.js or Python FastAPI for database interaction
├── frontend/          # Next.js React application
└── database/          # SQL schemas and migration scripts
```

## 2. Core Modules
- **Ingestion Module:** Downloads zips, extracts CSVs.
- **Transform Module:** Standardizes data types, handles nulls, calculates `authority_age`.
- **Database Layer:** Manages connections and batch inserts/upserts.
- **Filter Engine (API):** Dynamically builds SQL queries based on UI parameters.
- **UI Components:** Reusable React components for tables, filters, and charts.
