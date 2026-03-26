# Deployment Guide

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | ≥ 3.10 | `python3 --version` |
| Java (JDK) | ≥ 11 | `java -version` |
| Git | any | `git --version` |

Java is required by PySpark. On macOS: `brew install openjdk@17`

---

## 1. Clone the Repository

```bash
git clone https://github.com/TarjBaxi74/Food-Delivery-Analytics.git
cd Food-Delivery-Analytics
```

---

## 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows
```

---

## 3. Install Dependencies

```bash
pip install -e .
```

This installs all packages declared in `pyproject.toml`:
- `pyspark` — Bronze/Silver ETL
- `duckdb` — Analytical warehouse
- `dbt-duckdb` — Analytics marts
- `pandas`, `numpy`, `faker` — Data generation and profiling

Verify:
```bash
python3 -c "import pyspark, duckdb, dbt; print('OK')"
```

---

## 4. Install dbt Packages

```bash
cd dbt_project
dbt deps
cd ..
```

Installs `dbt_utils` (declared in `packages.yml`).

---

## 5. Configure the Warehouse Path

`dbt_project/profiles.yml` uses a relative path by default:

```yaml
food_delivery:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: '../data/warehouse/analytics.duckdb'
      threads: 4
      schema: main
```

**dbt must be run from inside `dbt_project/`** — the relative path resolves to `data/warehouse/analytics.duckdb` at the project root. No changes needed for a standard clone.

---

## 6. Run the Full Pipeline

### Option A — One command (recommended)

```bash
python3 demo.py
```

Runs all 6 steps in sequence and prints a live summary.

### Option B — Step by step via Make

```bash
make generate   # Step 1: generate synthetic data  (~30s)
make spark      # Step 2: Bronze → Silver ETL       (~30s)
make load       # Step 3: QA profile + DuckDB load  (~5s)
make dbt        # Step 4: dbt run + dbt test        (~15s)
```

### Option C — Step by step via Python

```bash
python3 -m src.generators.orchestrator         # generate data
python3 -m src.spark_jobs.run_pipeline         # Bronze → Silver
python3 -m src.loaders.silver_to_duckdb        # load to DuckDB
cd dbt_project && dbt run && dbt test && cd .. # build marts
```

---

## 7. Verify the Pipeline

### Check Silver output (3 joined tables)

```bash
ls data/silver/
# order_facts/  delivery_ops/  restaurant_support/
```

### Check DuckDB warehouse

```bash
python3 -c "
import duckdb
con = duckdb.connect('data/warehouse/analytics.duckdb', read_only=True)
for (t,) in con.execute('SHOW TABLES').fetchall(): print(t)
"
```

Expected output:
```
delivery_ops
order_facts
restaurant_support
```

### Check dbt marts

```bash
cd dbt_project && dbt test
# Expected: PASS=37 WARN=0 ERROR=0
```

---

## 8. Generate dbt Documentation (Optional)

```bash
cd dbt_project
dbt docs generate
dbt docs serve        # Opens http://localhost:8080
```

The docs site shows the full model DAG, column descriptions, and test results.

---

## 9. Deploy dbt Docs to GitHub Pages

The `docs/` directory at the root contains a pre-built static site.

### Regenerate and push

```bash
make gh-pages         # rebuilds docs/index.html from dbt target/
git add docs/
git commit -m "Update dbt docs"
git push origin main
```

### Enable GitHub Pages

In the repository settings:
- **Source:** Deploy from branch
- **Branch:** `main`
- **Folder:** `/docs`

The live docs site will be available at:
```
https://<username>.github.io/<repo-name>/
```

---

## 10. Clean and Re-run

```bash
make clean            # removes all data/bronze, silver, warehouse, dbt artifacts
make demo             # re-runs the full pipeline from scratch
```

---

## Directory Structure After Deployment

```
data/
├── raw/                     # Generated CSVs + JSON (gitignored)
│   ├── orders.csv
│   ├── delivery_events.json
│   └── ...
├── bronze/                  # Parquet + batch metadata (gitignored)
│   ├── orders/
│   ├── delivery_events/
│   └── ...
├── silver/                  # 3 joined Parquet tables (gitignored)
│   ├── order_facts/
│   ├── delivery_ops/
│   └── restaurant_support/
└── warehouse/
    └── analytics.duckdb     # DuckDB warehouse (gitignored)

dbt_project/
└── target/                  # dbt compiled + run artifacts (gitignored)
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'pandas'`**
The active Python and the one pip installed to are different. Run:
```bash
which python3 && python3 -m pip install -e .
```

**`PYTHON_VERSION_MISMATCH` from PySpark**
PySpark workers are picking up a different Python binary. Set:
```bash
export PYSPARK_PYTHON=$(which python3)
export PYSPARK_DRIVER_PYTHON=$(which python3)
```

**`No files found that match the pattern .../*.parquet`**
Silver is empty — the Spark step didn't complete. Re-run:
```bash
make spark
```

**`dbt profiles.yml` path error**
dbt must be run from inside `dbt_project/`. All Make targets handle this automatically. If running manually, `cd dbt_project` first.

**Java not found (PySpark fails to start)**
```bash
brew install openjdk@17
export JAVA_HOME=$(/usr/libexec/java_home)
```
