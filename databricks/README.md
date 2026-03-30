# Databricks Free Edition Deployment Guide

This directory contains the Databricks notebooks for deploying the Food Delivery Analytics pipeline on Databricks Free Edition.

## ⚠️ Important: DBFS Disabled Fix

**DBFS is disabled in Databricks Free Edition!** The notebooks have been updated to use **Spark Tables** instead of DBFS paths.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  DATABRICKS FREE EDITION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────────────┐    │
│  │  01_Data_Generation │───▶│  02_Bronze_Ingestion        │    │
│  │     _Daily.ipynb    │    │       (Spark Tables)        │    │
│  └─────────────────────┘    └──────────────┬──────────────┘    │
│                                             │                   │
│                                             ▼                   │
│  ┌─────────────────────┐    ┌─────────────────────────────┐    │
│  │  05_Pipeline_       │◀───│  04_DBT_Models              │    │
│  │  Orchestrator.ipynb │    │  (Views + Tables)           │    │
│  └─────────────────────┘    └─────────────────────────────┘    │
│                                                                  │
│  STORAGE: Spark Tables (not DBFS)                               │
│  - bronze_* tables (raw data)                                   │
│  - silver_* tables (cleaned data)                               │
│  - fct_*, mart_* tables (analytics)                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Spark Tables Created

### Bronze Layer (Raw)
- `bronze_restaurants` - Master restaurant data
- `bronze_riders` - Master rider data
- `bronze_orders` - Daily orders (appended)
- `bronze_order_items` - Daily order items (appended)
- `bronze_delivery_events` - Daily events (appended)
- `bronze_refunds` - Daily refunds (appended)
- `bronze_support_tickets` - Daily tickets (appended)

### Silver Layer (Cleaned)
- `silver_orders_clean` - Deduplicated, cleaned orders
- `silver_order_items_agg` - Aggregated items per order
- `silver_refunds_agg` - Aggregated refunds per order
- `silver_delivery_events` - Events with rider context
- `silver_restaurants` - Deduplicated restaurants
- `silver_support_tickets` - Tickets with restaurant context

### Analytics Layer
- `fct_orders` - Fact table with delivery timeline
- `mart_sla_breach_analysis` - SLA breach by city/time
- `mart_weekly_trends` - Weekly business metrics

## Setup Steps

### Step 1: Install Packages

In a new notebook cell:

```python
%pip install faker pandas numpy
```

### Step 2: Run Notebooks in Order

Run these notebooks sequentially:

1. **01_Data_Generation_Daily.ipynb** - Generates daily data → saves to Spark tables
2. **02_Bronze_Ingestion.ipynb** - Processes raw data → creates silver_* tables
3. **03_Silver_Transformation.ipynb** - Builds final silver tables with joins
4. **04_DBT_Models.ipynb** - Creates analytics views and tables

### Step 3: Schedule (Optional)

1. Go to **Jobs** → **Create Job**
2. Add tasks for each notebook
3. Set schedule (e.g., daily at 2 AM)

## Quick Test

Run this to verify everything works:

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

# Check tables
tables = spark.catalog.listTables()
for t in tables:
    if 'silver' in t.name or 'bronze' in t.name or 'mart' in t.name or 'fct' in t.name:
        print(f"{t.name}: {t.tableType}")
```

## Notebook Descriptions

| Notebook | Purpose |
|----------|---------|
| `01_Data_Generation_Daily.ipynb` | Generate synthetic data → Spark tables |
| `02_Bronze_Ingestion.ipynb` | Clean & deduplicate → silver_* tables |
| `03_Silver_Transformation.ipynb` | Build joined silver tables |
| `04_DBT_Models.ipynb` | Create analytics views & tables |
| `05_Pipeline_Orchestrator.ipynb` | Orchestrate full pipeline |

## Troubleshooting

| Error | Solution |
|-------|----------|
| DBFS disabled | Use Spark Tables (not DBFS paths) |
| Table not found | Run previous notebooks first |
| Out of memory | Reduce data volume in CONFIG |

## Files

```
databricks/
├── 01_Data_Generation_Daily.ipynb
├── 02_Bronze_Ingestion.ipynb
├── 03_Silver_Transformation.ipynb
├── 04_DBT_Models.ipynb
├── 05_Pipeline_Orchestrator.ipynb
├── README.md
└── setup_environment.py
```