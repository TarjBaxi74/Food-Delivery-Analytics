import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import duckdb
from config.settings import PATHS

# The 3 silver tables produced by the Spark pipeline.
# Each maps to one joined Parquet directory.
SILVER_TABLES = [
    "order_facts",          # orders + order_items (agg) + refunds
    "delivery_ops",         # delivery_events + riders
    "restaurant_support",   # support_tickets + orders → restaurants
]


def load_silver_to_duckdb():
    silver_path = PATHS["silver"]
    db_path = str(PATHS["warehouse"])

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(db_path)

    print("Loading silver tables into DuckDB...")

    for table in SILVER_TABLES:
        parquet_path = silver_path / table
        if not parquet_path.exists():
            print(f"  WARNING: {parquet_path} not found, skipping")
            continue
        con.execute(f"DROP TABLE IF EXISTS {table}")
        # order_facts is date-partitioned; the others are flat
        glob = f"{parquet_path}/**/*.parquet"
        con.execute(f"""
            CREATE TABLE {table} AS
            SELECT * FROM read_parquet('{glob}', hive_partitioning=true)
        """)
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  Loaded {table}: {count:,} rows")

    print("\nDuckDB warehouse tables:")
    for (t,) in con.execute("SHOW TABLES").fetchall():
        print(f"  - {t}")

    con.close()
    print(f"\nWarehouse saved to {db_path}")


if __name__ == "__main__":
    load_silver_to_duckdb()
