# Complete Databricks Deployment Steps

## ✅ Fixed Issue: `include_groups` Error

The `include_groups=False` parameter error has been fixed. The notebooks now use a simpler approach compatible with all pandas versions.

---

## Step-by-Step Deployment

### Step 1: Access Databricks

1. Go to **https://community.cloud.databricks.com/** (Free Edition)
2. Sign in or create account
3. You'll see your workspace

---

### Step 2: Upload Notebooks

1. Click **Workspace** (left sidebar)
2. Navigate to your user folder
3. Right-click → **Import**
4. Upload these 5 files:
   - `01_Data_Generation_Daily.ipynb`
   - `02_Bronze_Ingestion.ipynb`
   - `03_Silver_Transformation.ipynb`
   - `04_DBT_Models.ipynb`
   - `05_Pipeline_Orchestrator.ipynb`

---

### Step 3: Create a Cluster OR Use Serverless

**Option A: Serverless Compute (Recommended for Free Tier)**
- No setup needed!
- Just attach notebooks to "Serverless" when running
- ✅ Notebooks are already compatible

**Option B: Create Your Own Cluster**
1. Click **Compute** (left sidebar)
2. Click **Create Cluster**
3. Settings:
   - **Name**: `food-delivery-cluster`
   - **Runtime**: Latest (e.g., 14.3 LTS)
   - **Node type**: Smallest available
4. Click **Create Cluster**
5. Wait ~5 minutes for it to start

---

### Step 4: Install Packages

1. Open any notebook
2. **Attach to Serverless** (or your cluster) - dropdown at top
3. Run this in a cell:

```python
%pip install faker pandas numpy
```

**Note**: On serverless compute, packages install automatically per session.

---

### Step 5: Run Notebooks in Order

#### Notebook 1: Data Generation

```
Open: 01_Data_Generation_Daily.ipynb
Attach to: Serverless (or your cluster)
Click: Run All
```

**What it does:**
- Generates ~1000 orders for today
- Creates 7 Bronze tables:
  - `bronze_restaurants`
  - `bronze_riders`
  - `bronze_orders`
  - `bronze_order_items`
  - `bronze_delivery_events`
  - `bronze_refunds`
  - `bronze_support_tickets`

**Expected output:**
```
Generated 150 restaurants
Generated 300 riders
Generated 1234 orders for 2024-03-30
...
✓ bronze_orders: 1234 rows
```

---

#### Notebook 2: Bronze Processing

```
Open: 02_Bronze_Ingestion.ipynb
Click: Run All
```

**What it does:**
- Cleans and deduplicates data
- Creates 6 Silver tables:
  - `silver_orders_clean`
  - `silver_order_items_agg`
  - `silver_refunds_agg`
  - `silver_delivery_events`
  - `silver_restaurants`
  - `silver_support_tickets`

---

#### Notebook 3: Silver Transformation

```
Open: 03_Silver_Transformation.ipynb
Click: Run All
```

**What it does:**
- Builds final joined Silver tables:
  - `silver_order_facts` (orders + items + refunds)
  - `silver_delivery_ops` (events + riders)
  - `silver_restaurant_support` (tickets + restaurants)

---

#### Notebook 4: Analytics Models

```
Open: 04_DBT_Models.ipynb
Click: Run All
```

**What it does:**
- Creates analytics views and tables:
  - `stg_orders`, `stg_delivery_events`, `stg_restaurants` (views)
  - `fct_orders` (fact table)
  - `mart_sla_breach_analysis` (SLA metrics)
  - `mart_weekly_trends` (weekly business metrics)

---

### Step 6: Verify Everything Works

Run this in a new cell:

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

print("=== All Tables ===")
tables = spark.catalog.listTables()
for t in sorted(tables, key=lambda x: x.name):
    if any(prefix in t.name for prefix in ['bronze', 'silver', 'mart', 'fct', 'stg']):
        count = spark.table(t.name).count()
        print(f"  {t.name}: {count:,} rows")
```

**Expected output:**
```
=== All Tables ===
  bronze_delivery_events: 8,000 rows
  bronze_order_items: 3,500 rows
  bronze_orders: 1,234 rows
  bronze_refunds: 98 rows
  bronze_restaurants: 150 rows
  bronze_riders: 300 rows
  bronze_support_tickets: 62 rows
  fct_orders: 1,234 rows
  mart_sla_breach_analysis: 40 rows
  mart_weekly_trends: 10 rows
  silver_delivery_ops: 8,000 rows
  silver_order_facts: 1,234 rows
  silver_restaurant_support: 62 rows
  ...
```

---

### Step 7: Query Your Data

Try these queries:

```python
# SLA breach analysis
spark.sql("""
    SELECT city, time_slot, total_orders, breach_rate_pct
    FROM mart_sla_breach_analysis
    ORDER BY breach_rate_pct DESC
    LIMIT 5
""").show()

# Weekly trends
spark.sql("""
    SELECT week_start, total_orders, completed_orders, gmv
    FROM mart_weekly_trends
    ORDER BY week_start DESC
    LIMIT 5
""").show()

# Top restaurants by orders
spark.sql("""
    SELECT restaurant_id, city, COUNT(*) as order_count
    FROM fct_orders
    GROUP BY restaurant_id, city
    ORDER BY order_count DESC
    LIMIT 10
""").show()
```

---

### Step 8: Schedule Daily Pipeline (Optional)

1. Click **Workflows** → **Jobs** (left sidebar)
2. Click **Create Job**
3. **Job name**: `Food Delivery Daily Pipeline`
4. Add tasks:
   - Task 1: `01_Data_Generation_Daily`
   - Task 2: `02_Bronze_Ingestion` (depends on Task 1)
   - Task 3: `03_Silver_Transformation` (depends on Task 2)
   - Task 4: `04_DBT_Models` (depends on Task 3)
5. **Schedule**: Daily at 2:00 AM
6. Click **Create**

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'faker'` | Run `%pip install faker pandas numpy` |
| `Table not found: bronze_orders` | Run Notebook 1 first |
| `DBFS disabled` | ✅ Already fixed - uses Spark tables |
| `include_groups` error | ✅ Already fixed in notebooks |
| `JVM_ATTRIBUTE_NOT_SUPPORTED` | ✅ Already fixed - use Serverless compute |
| `sparkContext not supported` | ✅ Already fixed - removed from notebooks |
| Cluster not starting | Use Serverless instead, or wait 5-10 minutes |

---

## What Each Table Contains

### Bronze Layer (Raw Data)
- **bronze_orders**: Daily orders with timestamps
- **bronze_order_items**: Items per order
- **bronze_delivery_events**: Event timeline per order
- **bronze_refunds**: Refund records
- **bronze_restaurants**: Restaurant master data
- **bronze_riders**: Rider master data
- **bronze_support_tickets**: Customer support tickets

### Silver Layer (Cleaned & Joined)
- **silver_order_facts**: Orders + items + refunds (one row per order)
- **silver_delivery_ops**: Events + rider context
- **silver_restaurant_support**: Tickets + restaurant context

### Analytics Layer
- **fct_orders**: Fact table with delivery timeline
- **mart_sla_breach_analysis**: SLA metrics by city/time
- **mart_weekly_trends**: Weekly business KPIs

---

## Daily Incremental Loading

Each day:
1. Notebook 1 generates new data → **appends** to Bronze tables
2. Notebook 2-4 process all data → **overwrites** Silver/Analytics tables

This gives you a growing dataset over time!

---

## Next Steps

1. ✅ Run all 4 notebooks
2. ✅ Verify tables exist
3. ✅ Query your data
4. 📊 Connect to BI tool (Tableau, Power BI)
5. 📅 Schedule daily job
6. 🚀 Scale up cluster for more data

---

## Files in This Directory

```
databricks/
├── 01_Data_Generation_Daily.ipynb    ← Start here
├── 02_Bronze_Ingestion.ipynb         ← Run second
├── 03_Silver_Transformation.ipynb    ← Run third
├── 04_DBT_Models.ipynb               ← Run fourth
├── 05_Pipeline_Orchestrator.ipynb    ← Optional: runs all
├── DEPLOYMENT_STEPS.md               ← This file
├── README.md                         ← Architecture overview
└── TEST_LOCALLY.py                   ← Local test (optional)
```

---

**Ready to deploy!** 🚀

Upload the notebooks and follow the steps above.