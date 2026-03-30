# ✅ Deployment Checklist

Use this checklist to ensure successful deployment to Databricks.

---

## Pre-Deployment

### Local Setup
- [ ] All notebook files present in `databricks/` folder
- [ ] Git repository initialized and up to date
- [ ] Code pushed to GitHub (if using Repos or GitHub Actions)

### Files to Deploy
- [ ] `01_Data_Generation_Daily.ipynb`
- [ ] `02_Bronze_Ingestion.ipynb`
- [ ] `03_Silver_Transformation.ipynb`
- [ ] `04_DBT_Models.ipynb`
- [ ] `05_Pipeline_Orchestrator.ipynb` (optional)

### Documentation
- [ ] `QUICK_START.md` - Quick reference
- [ ] `DEPLOYMENT_STEPS.md` - Detailed guide
- [ ] `GIT_SYNC_SETUP.md` - Auto-deploy options
- [ ] `CONTEXT_SUMMARY.md` - Complete overview

---

## Databricks Setup

### Account & Workspace
- [ ] Databricks Community Edition account created
- [ ] Logged into https://community.cloud.databricks.com/
- [ ] Workspace accessible

### Compute
- [ ] Serverless compute available (recommended)
- [ ] OR cluster created (if not using serverless)

---

## Deployment Method

Choose ONE method:

### Option A: Manual Upload (Fastest)
- [ ] Navigate to Workspace → Your folder
- [ ] Right-click → Import
- [ ] Upload all 5 notebook files
- [ ] Notebooks visible in workspace

### Option B: Databricks Repos (Recommended)
- [ ] Code pushed to GitHub
- [ ] In Databricks: Repos → Add Repo
- [ ] GitHub URL entered
- [ ] Repo connected successfully
- [ ] Notebooks visible at `/Repos/YOUR_USERNAME/YOUR_REPO/databricks/`

### Option C: Databricks CLI
- [ ] Databricks CLI installed: `pip install databricks-cli`
- [ ] CLI configured: `databricks configure --token`
- [ ] Token generated from User Settings → Access Tokens
- [ ] Sync script executed: `./sync_to_databricks.sh`
- [ ] Notebooks uploaded successfully

### Option D: GitHub Actions (CI/CD)
- [ ] GitHub secrets configured:
  - [ ] `DATABRICKS_HOST`
  - [ ] `DATABRICKS_TOKEN`
  - [ ] `DATABRICKS_USER`
- [ ] Workflow file in `.github/workflows/deploy-databricks.yml`
- [ ] Push to main branch triggers deployment
- [ ] Workflow runs successfully

---

## Initial Setup

### Package Installation
- [ ] Open any notebook
- [ ] Attach to Serverless (or cluster)
- [ ] Run: `%pip install faker pandas numpy`
- [ ] Packages installed successfully

### Environment Test
- [ ] Create test cell with:
  ```python
  import faker
  import pandas as pd
  import numpy as np
  from pyspark.sql import SparkSession
  spark = SparkSession.builder.getOrCreate()
  print("✅ Environment ready!")
  ```
- [ ] Cell executes without errors

---

## Pipeline Execution

### Notebook 1: Data Generation
- [ ] Open `01_Data_Generation_Daily.ipynb`
- [ ] Attach to Serverless
- [ ] Click "Run All"
- [ ] Execution completes successfully
- [ ] Output shows:
  - [ ] Generated ~150 restaurants
  - [ ] Generated ~300 riders
  - [ ] Generated ~1000 orders
  - [ ] 7 Bronze tables created

### Notebook 2: Bronze Ingestion
- [ ] Open `02_Bronze_Ingestion.ipynb`
- [ ] Click "Run All"
- [ ] Execution completes successfully
- [ ] Output shows:
  - [ ] Data cleaned and deduplicated
  - [ ] 6 Silver intermediate tables created

### Notebook 3: Silver Transformation
- [ ] Open `03_Silver_Transformation.ipynb`
- [ ] Click "Run All"
- [ ] Execution completes successfully
- [ ] Output shows:
  - [ ] 3 final Silver tables created:
    - [ ] `silver_order_facts`
    - [ ] `silver_delivery_ops`
    - [ ] `silver_restaurant_support`

### Notebook 4: Analytics Models
- [ ] Open `04_DBT_Models.ipynb`
- [ ] Click "Run All"
- [ ] Execution completes successfully
- [ ] Output shows:
  - [ ] 3 staging views created
  - [ ] 3 mart tables created:
    - [ ] `fct_orders`
    - [ ] `mart_sla_breach_analysis`
    - [ ] `mart_weekly_trends`

---

## Verification

### Table Count Check
- [ ] Run verification query:
  ```python
  from pyspark.sql import SparkSession
  spark = SparkSession.builder.getOrCreate()
  
  tables = spark.catalog.listTables()
  print(f"Total tables: {len(tables)}")
  
  for t in sorted(tables, key=lambda x: x.name):
      if any(p in t.name for p in ['bronze', 'silver', 'mart', 'fct', 'stg']):
          count = spark.table(t.name).count()
          print(f"  {t.name}: {count:,} rows")
  ```
- [ ] Expected tables present:
  - [ ] 7 Bronze tables
  - [ ] 9 Silver tables
  - [ ] 5 Analytics tables/views

### Data Quality Check
- [ ] Run sample queries:
  ```sql
  -- SLA breach analysis
  SELECT * FROM mart_sla_breach_analysis LIMIT 5;
  
  -- Weekly trends
  SELECT * FROM mart_weekly_trends LIMIT 5;
  
  -- Order facts
  SELECT * FROM fct_orders LIMIT 5;
  ```
- [ ] Queries return data
- [ ] Data looks reasonable

### Performance Check
- [ ] Notebook 1 completes in < 5 minutes
- [ ] Notebook 2 completes in < 3 minutes
- [ ] Notebook 3 completes in < 3 minutes
- [ ] Notebook 4 completes in < 2 minutes

---

## Scheduling (Optional)

### Create Daily Job
- [ ] Navigate to Workflows → Jobs
- [ ] Click "Create Job"
- [ ] Job name: `Food Delivery Daily Pipeline`
- [ ] Add tasks:
  - [ ] Task 1: `01_Data_Generation_Daily`
  - [ ] Task 2: `02_Bronze_Ingestion` (depends on Task 1)
  - [ ] Task 3: `03_Silver_Transformation` (depends on Task 2)
  - [ ] Task 4: `04_DBT_Models` (depends on Task 3)
- [ ] Schedule: Daily at 2:00 AM UTC
- [ ] Email notifications configured
- [ ] Job created and enabled

### Test Job
- [ ] Click "Run Now"
- [ ] Job executes successfully
- [ ] All tasks complete
- [ ] Data updated

---

## Post-Deployment

### Documentation
- [ ] Team members have access to documentation
- [ ] QUICK_START.md shared with team
- [ ] Deployment process documented

### Monitoring
- [ ] Job runs monitored
- [ ] Failure alerts configured
- [ ] Data quality checks in place

### Next Steps
- [ ] Connect BI tool (Tableau, Power BI)
- [ ] Build dashboards
- [ ] Share insights with stakeholders

---

## Troubleshooting

If you encounter issues, check:

- [ ] All packages installed: `faker`, `pandas`, `numpy`
- [ ] Notebooks run in correct order (1 → 2 → 3 → 4)
- [ ] Serverless compute selected (or cluster running)
- [ ] Previous notebook completed before running next
- [ ] Sufficient workspace storage available

Common errors and solutions:
- **ModuleNotFoundError**: Install packages with `%pip install`
- **Table not found**: Run previous notebooks first
- **Out of memory**: Reduce data volume in CONFIG
- **Timeout**: Increase timeout or use larger cluster

---

## Success Criteria

✅ Deployment is successful when:
- All 5 notebooks uploaded and accessible
- All 4 notebooks execute without errors
- 21 tables/views created (7 Bronze + 9 Silver + 5 Analytics)
- Sample queries return data
- Daily job scheduled (optional)

---

## Support

If you need help:
1. Check `DEPLOYMENT_STEPS.md` for detailed instructions
2. Review `CONTEXT_SUMMARY.md` for complete overview
3. Check Databricks documentation
4. Review error messages in notebook output

---

**Last Updated**: March 30, 2026

**Status**: Ready for deployment ✅
