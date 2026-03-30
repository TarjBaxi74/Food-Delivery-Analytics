#!/usr/bin/env python3
"""
Databricks Environment Setup Script
=====================================
Run this once to set up the Databricks environment for the pipeline.
"""

# Databricks Setup Checklist
SETUP_CHECKLIST = """
╔══════════════════════════════════════════════════════════════════════════════╗
║              FOOD DELIVERY PIPELINE - DATABRICKS SETUP                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

PREREQUISITES:
□ Databricks Free Edition account
□ DBFS storage enabled
□ Python 3.8+ runtime

STEP 1: CREATE DBFS DIRECTORIES
────────────────────────────────
Run in a Databricks notebook:

    dbutils.fs.mkdirs("/mnt/food-delivery-raw/daily/")
    dbutils.fs.mkdirs("/mnt/food-delivery-bronze/")
    dbutils.fs.mkdirs("/mnt/food-delivery-silver/")
    dbutils.fs.mkdirs("/mnt/food-delivery-dbt/")
    dbutils.fs.mkdirs("/mnt/food-delivery-logs/")


STEP 2: INSTALL PACKAGES
─────────────────────────
    %pip install dbt-databricks faker pandas numpy pyspark


STEP 3: CONFIGURE DBT
──────────────────────
Set environment variables:

    import os
    os.environ["DATABRICKS_HOST"] = "https://your-workspace.cloud.databricks.com"
    os.environ["DATABRICKS_HTTP_PATH"] = "/sql/1.0/warehouses/your-warehouse-id"
    os.environ["DATABRICKS_TOKEN"] = "your-personal-access-token"

Where to find values:
- HOST: Your Databricks workspace URL
- HTTP_PATH: SQL Warehouses → Create Warehouse → Copy JDBC URL
- TOKEN: Settings → Developer → Generate Token


STEP 4: UPLOAD NOTEBOOKS
─────────────────────────
1. Import the 5 .ipynb files from this directory
2. Place in: /Workspace/Users/your-email/databricks/


STEP 5: CREATE SCHEDULED JOB
─────────────────────────────
1. Go to: Jobs → Create Job
2. Name: "Food Delivery Daily Pipeline"
3. Task: Notebook → Select 05_Pipeline_Orchestrator.ipynb
4. Schedule: 0 2 * * * (Daily at 2 AM)
5. Create


STEP 6: VERIFY
──────────────
Run the orchestrator notebook manually once to verify:
    %run /Workspace/Users/.../databricks/05_Pipeline_Orchestrator


╔══════════════════════════════════════════════════════════════════════════════╗
║                           QUICK START COMMANDS                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

# In Databricks notebook cell 1:
%pip install dbt-databricks faker pandas numpy

# In cell 2:
import os
os.environ["DATABRICKS_HOST"] = "https://<workspace>.cloud.databricks.com"
os.environ["DATABRICKS_HTTP_PATH"] = "/sql/1.0/warehouses/<warehouse-id>"
os.environ["DATABRICKS_TOKEN"] = "<token>"

# In cell 3:
dbutils.fs.mkdirs("/mnt/food-delivery-raw/daily/")
dbutils.fs.mkdirs("/mnt/food-delivery-bronze/")
dbutils.fs.mkdirs("/mnt/food-delivery-silver/")
dbutils.fs.mkdirs("/mnt/food-delivery-dbt/")
dbutils.fs.mkdirs("/mnt/food-delivery-logs/")

# Run pipeline
%run /Workspace/Users/.../databricks/05_Pipeline_Orchestrator

"""

if __name__ == "__main__":
    print(SETUP_CHECKLIST)