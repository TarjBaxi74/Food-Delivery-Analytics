# 🚀 Quick Start Guide - Databricks Serverless

## ✅ All Issues Fixed

- ✅ DBFS disabled → Using Spark tables
- ✅ `include_groups` error → Fixed in code
- ✅ `sparkContext` not supported → Removed from notebooks
- ✅ Serverless compatible → All notebooks ready

---

## 3-Minute Setup

### 1. Upload Notebooks (2 min)

1. Go to **Databricks Community Edition**: https://community.cloud.databricks.com/
2. Click **Workspace** → Your user folder
3. Right-click → **Import**
4. Upload these 5 files:
   - `01_Data_Generation_Daily.ipynb`
   - `02_Bronze_Ingestion.ipynb`
   - `03_Silver_Transformation.ipynb`
   - `04_DBT_Models.ipynb`
   - `05_Pipeline_Orchestrator.ipynb`

### 2. Install Packages (1 min)

Open any notebook and run:

```python
%pip install faker pandas numpy
```

### 3. Run Pipeline

**Attach to Serverless** (dropdown at top), then run each notebook:

```
01_Data_Generation_Daily.ipynb    → Click "Run All"
02_Bronze_Ingestion.ipynb         → Click "Run All"
03_Silver_Transformation.ipynb    → Click "Run All"
04_DBT_Models.ipynb               → Click "Run All"
```

---

## What You'll Get

After running all 4 notebooks:

### 📊 Data Generated
- ~1,000 orders for today
- ~8,000 delivery events
- ~100 refunds
- ~60 support tickets

### 🗄️ Tables Created (21 tables)

**Bronze Layer (7 tables)**
```
bronze_restaurants
bronze_riders
bronze_orders
bronze_order_items
bronze_delivery_events
bronze_refunds
bronze_support_tickets
```

**Silver Layer (6 tables)**
```
silver_orders_clean
silver_order_items_agg
silver_refunds_agg
silver_delivery_events
silver_restaurants
silver_support_tickets
```

**Final Silver (3 joined tables)**
```
silver_order_facts
silver_delivery_ops
silver_restaurant_support
```

**Analytics Layer (5 tables)**
```
stg_orders (view)
stg_delivery_events (view)
stg_restaurants (view)
fct_orders (table)
mart_sla_breach_analysis (table)
mart_weekly_trends (table)
```

---

## Verify It Works

Run this query:

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

# Check all tables
tables = spark.catalog.listTables()
print(f"Total tables created: {len(tables)}")

# Show sample data
spark.sql("""
    SELECT city, time_slot, total_orders, breach_rate_pct
    FROM mart_sla_breach_analysis
    ORDER BY breach_rate_pct DESC
    LIMIT 5
""").show()
```

---

## Query Examples

### SLA Breach Analysis
```sql
SELECT city, time_slot, total_orders, breach_rate_pct
FROM mart_sla_breach_analysis
ORDER BY breach_rate_pct DESC
```

### Weekly Business Trends
```sql
SELECT week_start, total_orders, completed_orders, gmv
FROM mart_weekly_trends
ORDER BY week_start DESC
```

### Top Restaurants
```sql
SELECT restaurant_id, city, COUNT(*) as orders
FROM fct_orders
GROUP BY restaurant_id, city
ORDER BY orders DESC
LIMIT 10
```

### Delivery Timeline
```sql
SELECT 
    order_id,
    city,
    order_ts,
    delivered_ts,
    total_time_minutes,
    is_sla_breached
FROM fct_orders
WHERE status = 'delivered'
LIMIT 10
```

---

## Daily Incremental Loading

Run **Notebook 1** daily to add new data:
- Each run adds ~1,000 new orders
- Data accumulates over time
- Analytics tables refresh automatically

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Can't find "Serverless" option | Use Databricks Community Edition (free) |
| Package install fails | Restart notebook and try again |
| Table not found | Run previous notebooks first |
| Out of memory | Reduce data volume in CONFIG |

---

## Next Steps

1. ✅ Run all 4 notebooks
2. 📊 Query your data
3. 📅 Schedule daily job (optional)
4. 🔗 Connect BI tool (Tableau, Power BI)
5. 📈 Build dashboards

---

## Files Reference

```
databricks/
├── 01_Data_Generation_Daily.ipynb    ← Start here
├── 02_Bronze_Ingestion.ipynb         
├── 03_Silver_Transformation.ipynb    
├── 04_DBT_Models.ipynb               
├── 05_Pipeline_Orchestrator.ipynb    ← Optional
├── QUICK_START.md                    ← This file
├── DEPLOYMENT_STEPS.md               ← Detailed guide
├── SERVERLESS_NOTES.md               ← Serverless info
└── README.md                         ← Architecture
```

---

**You're ready to go!** 🎉

Just upload the notebooks and run them in order.