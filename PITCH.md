# Food Delivery Operations Analytics
## Senior Review — Architecture Walkthrough & Demo Guide

> **Format:** 5–10 minute walkthrough
> **Audience:** Senior engineer / tech lead
> **Goal:** Show a production-grade data pipeline end-to-end, from raw data generation through analytics marts

---

## The Business Problem

> *"Food delivery platforms generate massive operational data, but turning it into actionable insight requires a real data pipeline — not just queries on a spreadsheet."*

Three questions this system answers in real-time:

1. **Where are deliveries failing SLA?** → By city and time slot
2. **What is driving refund spend?** → Root-cause breakdown
3. **Which restaurants and riders are underperforming?** → Risk tiering

---

## Architecture Overview

```
Raw Sources (7)       Bronze (7)          Silver (3 joined)     QA Profile    Warehouse       BI Marts
───────────────       ──────────          ─────────────────     ──────────    ─────────       ────────
orders.csv     ──►                ──►     order_facts       ──► Anomaly   ──► DuckDB    ──►  mart_sla_breach
order_items    ──►   Parquet +    ──►   (orders + items     ──► Checker   ──► (columnar)──►  mart_refunds
refunds        ──►   metadata     ──►    + refunds)             7 checks              ──►   mart_riders
               ──►   batch_id     ──►                                                  ──►  mart_restaurants
events.json    ──►   ingested_at  ──►     delivery_ops                                 ──►  mart_weekly_trends
riders         ──►                ──►   (events + riders)
               ──►                ──►
restaurants    ──►                ──►     restaurant_support
support_tickets──►                ──►   (tickets→orders→restaurants)

[Faker/NumPy]      [PySpark]          [PySpark joins]       [Pandas]      [DuckDB]        [dbt SQL]
```

**Stack:** Python · PySpark · DuckDB · dbt · Parquet
**Scale (demo):** 83,463 orders · 625,891 events · 8 cities · 10 weeks of data

---

## Walkthrough — Step by Step

---

### STEP 1 — Synthetic Data Generation `(~30 seconds)`

**What to say:**
> *"Rather than using a static CSV, I built a realistic data generator. It models real operational patterns — lunch and dinner peaks, weekend volume spikes, and intentional data quality defects like nulls, duplicates, and orphan records. This lets us test the pipeline end-to-end without needing production data."*

**Command:**
```bash
python3 -m src.generators.orchestrator
```

**What gets generated:**

| File | Rows | Notes |
|------|------|-------|
| `orders.csv` | 83,463 | With `customer_id`, `promised_delivery_ts`, `payment_mode` |
| `delivery_events.json` | 625,891 | Nested JSON, one event per status transition |
| `refunds.csv` | 6,376 | 8% refund rate on eligible orders |
| `restaurants.csv` | 150 | 8 Indian cities, 8 cuisine types |
| `riders.csv` | 300 | 3 shift types, city-balanced |
| `support_tickets.csv` | 4,194 | Linked to orders |

**Key design decisions to highlight:**
- Orders include `promised_delivery_ts` so SLA breaches can be computed precisely
- `_will_breach_sla` flag is passed to the events generator to create realistic late deliveries
- Defects are injected at controlled rates (1% nulls, 0.5% duplicates) to test cleaning logic

---

### STEP 2 — Spark ETL: Bronze → Silver `(~30 seconds)`

**What to say:**
> *"The Spark pipeline follows the Medallion architecture. Bronze is raw ingestion with metadata — we add batch_id and ingested_at to every record, nothing is dropped. Silver is where we clean: deduplicate on order_id, flag DQ issues, and enforce the schema. Downstream models only ever touch Silver."*

**Command:**
```bash
python3 -m src.spark_jobs.run_pipeline
```

**Bronze layer — what it adds:**

```
+--------------------+----------+-----------------------+
| order_id           | batch_id | _ingested_at          |
+--------------------+----------+-----------------------+
| ORD-A3F8C21D0E2B   | 20260326 | 2026-03-26 18:35:04   |
```

**Silver layer — 3 joined tables (not 7 raw copies):**

| Silver Table | Source Tables Joined | Key Design Decision |
|-------------|---------------------|---------------------|
| `order_facts` | orders + order_items (agg) + refunds | One row per order with item_count, items_subtotal, has_refund, refund_amount |
| `delivery_ops` | delivery_events + riders | Events enriched with rider_city, rider_shift — no extra lookup needed downstream |
| `restaurant_support` | support_tickets → orders → restaurants | Tickets carry full restaurant context via the order join chain |

**DQ flags per table:**

| Table | Flag | Count |
|-------|------|-------|
| `order_facts` | `_dq_has_null_customer` | 0 |
| `order_facts` | `_dq_invalid_order_value` | 0 |
| `delivery_ops` | `_dq_orphan_order` | 6,289 (1.0%) |
| `delivery_ops` | `_dq_missing_rider` | 0 |

**Talking point:** *"The key design choice here is that we join at the Silver layer, not in dbt. Downstream models get pre-joined, pre-enriched data. Analysts write simpler queries; the complex join logic lives in one tested place."*

---

### STEP 3 — QA Profiling `(seconds)`

**What to say:**
> *"Before loading anything into the warehouse, I run a profiling pass over the Silver tables. This is a set of targeted anomaly checks that catch issues a schema test won't — statistical outliers, refund rate spikes by city, SLA breach concentration, orphan events. The checks run on Pandas and produce a structured report with OK / WARN / FAIL findings."*

**Module:** [src/profiling/anomaly_checker.py](src/profiling/anomaly_checker.py)

**7 checks implemented:**

| Check | What it detects | Severity trigger |
|-------|----------------|-----------------|
| `null_rate[col]` | Column null % above threshold | WARN ≥ 5%, FAIL ≥ 20% |
| `duplicates[key]` | Duplicate primary keys | WARN if any found |
| `order_value_outliers` | Orders > 3σ from mean | WARN if > 1% of rows |
| `refund_rate_by_city` | City refund rate > 2× fleet avg | WARN |
| `orphan_events` | Events with no matching order | FAIL if ≥ 5% |
| `rider_assignment_gaps` | Delivery events missing rider_id | FAIL if > 5% |
| `sla_breach_by_city` | City breach rate > 2× fleet avg | WARN |

**Sample output:**
```
  Profile: silver_order_facts
    [✓] null_rate[order_id]: 0.0% nulls
    [✓] null_rate[order_value]: 0.0% nulls
    [✓] duplicates[order_id]: no duplicates
    [✓] order_value_outliers: 0 orders (0.00%) beyond 3σ
    [✓] refund_rate_by_city: fleet avg 8.0%, no city anomalies

  Profile: silver_delivery_ops
    [⚠] orphan_events: 1.00% of events have no matching order (6,289 rows)
    [✓] rider_assignment_gaps: 0 delivery events missing rider_id
```

**Talking point:** *"This is the QA gate. A FAIL here halts the pipeline before bad data reaches the warehouse. A WARN logs and continues. It's informed by the actual anomalies I was checking for — not just 'is this column not null'."*

---

### STEP 4 — DuckDB Load `(< 1 second)`

**What to say:**
> *"The 3 Silver Parquet tables are loaded into DuckDB. Because we joined at the Silver layer, we load 3 tables instead of 7 — less I/O, simpler schema, and dbt staging views are just projections rather than joins."*

**Command:**
```bash
python3 -m src.loaders.silver_to_duckdb
```

**Result:**
```
  Loaded order_facts:        83,463 rows
  Loaded delivery_ops:      625,891 rows
  Loaded restaurant_support:  4,194 rows
```

**Talking point:** *"The warehouse is a single `.duckdb` file — portable, version-controllable in CI, queryable by any BI tool."*

---

### STEP 5 — dbt Modeling `(~13 seconds)`

**What to say:**
> *"dbt handles the transformation layer. Because Silver already did the joining, staging views are simple projections — stg_riders selects distinct riders out of delivery_ops, stg_refunds filters order_facts where has_refund = true. No join logic in staging; all join complexity is tested once in the Spark layer."*

**Command:**
```bash
cd dbt_project && dbt run && dbt test
```

**Model hierarchy:**

```
staging (views)                core (tables)             analytics marts (tables)
───────────────               ──────────────             ───────────────────────
stg_orders            ──►     fct_orders        ──►     mart_sla_breach_analysis
stg_delivery_events   ──►     dim_restaurants   ──►     mart_restaurant_prep_delays
stg_refunds           ──►     dim_riders        ──►     mart_refund_drivers
stg_restaurants       ──►     dim_date          ──►     mart_rider_performance
stg_riders                                      ──►     mart_weekly_trends
stg_order_items
stg_support_tickets
```

**Results:**
```
16 models built successfully
39 data tests passed
0 errors
```

**Talking point:** *"The 39 tests include not-null checks, referential integrity between fct_orders and dim_restaurants, and accepted-value checks on status. If anyone breaks the schema upstream, dbt catches it before it hits the mart."*

---

### STEP 5 — Business Insights `(walk through each query)`

**What to say:**
> *"Now here's the payoff. Every mart answers a question an ops manager would actually ask. Let me walk through each one."*

---

#### Q1: Where are SLA breaches concentrated?

```sql
SELECT city, time_slot, total_orders, breach_rate_pct
FROM main_analytics.mart_sla_breach_analysis
ORDER BY breach_rate_pct DESC LIMIT 3;
```

| city | time_slot | total_orders | breach_rate_pct |
|------|-----------|-------------|-----------------|
| HYDERABAD | dinner | 1,491 | **96.2%** |
| PUNE | lunch | 2,535 | **96.1%** |
| DELHI | dinner | 1,438 | **96.1%** |

> *"Hyderabad dinner slot has a 96% SLA breach rate. This tells ops to investigate whether it's a rider density problem, restaurant prep times, or routing — we can drill further."*

---

#### Q2: Which restaurants are causing prep delays?

```sql
SELECT restaurant_id, city, cuisine_type, delay_rate_pct, risk_category
FROM main_analytics.mart_restaurant_prep_delays
ORDER BY delay_rate_pct DESC LIMIT 3;
```

| restaurant_id | city | cuisine_type | delay_rate_pct | risk_category |
|--------------|------|-------------|----------------|--------------|
| REST-16910 | Mumbai | Biryani | **64.8%** | Medium Risk |
| REST-66835 | Ahmedabad | Chinese | **64.4%** | Medium Risk |
| REST-25305 | Kolkata | South Indian | **63.8%** | Medium Risk |

> *"Every restaurant here is flagged. A category manager can pull this list and trigger SLA review conversations with partners."*

---

#### Q3: What is driving refund spend?

```sql
SELECT refund_driver_category, refund_count, refund_count_pct, refund_amount
FROM main_analytics.mart_refund_drivers
ORDER BY refund_count_pct DESC;
```

| Category | Count | % of Refunds | Total Amount |
|----------|-------|-------------|--------------|
| Missing Items | 2,505 | **39.3%** | ₹3,32,622 |
| Delay | 2,174 | **34.1%** | ₹1,27,120 |
| Cancellation | 1,247 | **19.6%** | ₹3,58,269 |
| Other | 450 | 7.1% | ₹68,451 |

> *"Missing items alone drive 39% of refund volume but cancellations cost more per incident — ₹287 average vs ₹58 for delays. Different intervention strategies for each."*

---

#### Q4: Rider performance tiers

```sql
SELECT performance_tier, COUNT(*) as riders
FROM main_analytics.mart_rider_performance
GROUP BY performance_tier;
```

> *"With the current SLA thresholds, all 299 riders are flagged as 'At Risk'. That's not a rider problem — that's a systemic signal. The data is telling us that our promised delivery windows may be too aggressive for current capacity. This is exactly the kind of insight that should trigger a product review."*

---

#### Q5: Weekly GMV trends

```sql
SELECT week_start::DATE, total_orders, ROUND(gmv,0) as gmv, gmv_wow_pct
FROM main_analytics.mart_weekly_trends
ORDER BY week_start DESC LIMIT 5;
```

| Week | Orders | GMV (₹) | WoW % |
|------|--------|---------|-------|
| 2026-03-16 | 9,123 | 22,74,550 | -2.9% |
| 2026-03-09 | 9,489 | 23,41,812 | +13.9% |
| 2026-03-02 | 8,277 | 20,55,856 | -5.8% |
| 2026-02-23 | 8,747 | 21,82,664 | +9.0% |
| 2026-02-16 | 7,941 | 20,02,027 | -11.1% |

> *"GMV swings between ₹20L and ₹23L week-over-week. The WoW column is calculated in dbt using LAG() so it's always fresh when the pipeline runs."*

---

## End-to-End Runtime

```
Step 1 — Data generation:    31.6s
Step 2 — Spark ETL:          30.9s  (3 joined Silver tables)
Step 3 — QA Profiling:        ~2s   (7 anomaly checks, Pandas)
Step 4 — DuckDB load:          0.8s (3 tables instead of 7)
Step 5 — dbt models:          13.0s
Step 6 — Insights:           instant
──────────────────────────────────
Total:                        ~79s
```

**One command to reproduce everything:**
```bash
python3 demo.py
```

---

## What Makes This Production-Grade

| Aspect | What Was Built |
|--------|---------------|
| **Auditability** | Every Silver record carries `batch_id`, `_ingested_at`, `_source_file` |
| **DQ transparency** | Bad records flagged, never silently dropped |
| **QA profiling** | 7-check anomaly layer between Silver and warehouse — catches stat outliers, rate spikes, orphans |
| **Silver joins** | 7 raw tables → 3 purpose-built joined tables; join logic tested once in Spark, not scattered in dbt |
| **Idempotency** | Re-running `dbt run` produces the same result |
| **Testability** | 39 dbt schema tests; Python generators have seed control |
| **Separation of concerns** | Generator → Spark → Profiling → DuckDB → dbt — each layer replaceable |
| **Portability** | No cloud dependencies; entire pipeline runs locally in ~79 seconds |

---

## Potential Extensions

- **Airflow DAG** — schedule `generate → spark → load → dbt` as a daily pipeline
- **Superset / Metabase** — connect to `analytics.duckdb` for live dashboards
- **GitHub Actions** — run `dbt test` on every PR as a CI data quality gate
- **Streaming** — replace CSV ingestion with Kafka → Spark Structured Streaming

---

## Repository Structure

```
.
├── config/                  # Settings, data config
├── src/
│   ├── generators/          # Synthetic data (orders, events, refunds...)
│   ├── profiling/           # QA anomaly checker (7 checks on Silver tables)
│   ├── spark_jobs/          # Bronze and Silver Spark jobs
│   └── loaders/             # Silver → DuckDB loader
├── dbt_project/
│   ├── models/
│   │   ├── staging/         # stg_* views
│   │   ├── marts/           # dim_*, fct_* core tables
│   │   └── analytics/       # mart_* business answer tables
│   └── tests/               # Schema + data quality tests
├── tests/                   # Python unit tests
├── data/
│   ├── raw/                 # Generated CSVs / JSON
│   ├── bronze/              # Parquet + metadata
│   ├── silver/              # Cleaned Parquet
│   └── warehouse/           # analytics.duckdb
└── demo.py                  # One-command end-to-end demo
```

---

*Built with PySpark 4.0 · DuckDB 1.4 · dbt-duckdb 1.10 · Python 3.9*
