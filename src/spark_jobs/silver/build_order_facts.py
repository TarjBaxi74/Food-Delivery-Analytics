"""
Silver: order_facts
====================
Joins orders + order_items (aggregated) + refunds into one enriched table.

One row per order. Downstream consumers never need to join these three
bronze tables again.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, coalesce, trim, upper, lit,
    row_number, hour, dayofweek, current_timestamp,
    count, sum as _sum, round as _round, first
)
from pyspark.sql.window import Window


class OrderFactsBuilder:
    def __init__(self, spark: SparkSession, bronze_path: str, silver_path: str):
        self.spark = spark
        self.bronze_path = bronze_path
        self.silver_path = silver_path

    def build(self) -> DataFrame:
        orders    = self._clean_orders(self._read("orders"))
        items_agg = self._aggregate_items(self._read("order_items"))
        refunds   = self._aggregate_refunds(self._read("refunds"))

        df = (orders
              .join(items_agg, on="order_id", how="left")
              .join(refunds,   on="order_id", how="left"))

        df = df.fillna({"item_count": 0, "items_subtotal": 0.0,
                        "has_refund": False, "refund_amount": 0.0})
        return df

    def write(self, df: DataFrame) -> None:
        (df.write.mode("overwrite")
           .partitionBy("order_date")
           .parquet(f"{self.silver_path}/order_facts"))
        print(f"  Silver order_facts written ({df.count()} rows)")

    # ── private helpers ───────────────────────────────────────────────────────

    def _read(self, table: str) -> DataFrame:
        return self.spark.read.parquet(f"{self.bronze_path}/{table}")

    def _clean_orders(self, df: DataFrame) -> DataFrame:
        # Drop corrupt records
        if "_corrupt_record" in df.columns:
            df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")

        # Deduplicate: keep latest ingestion per order_id
        w = Window.partitionBy("order_id").orderBy(col("_ingested_at").desc())
        df = (df.withColumn("_rn", row_number().over(w))
                .filter(col("_rn") == 1)
                .drop("_rn"))

        # Standardise
        df = (df
              .withColumn("city",         upper(trim(col("city"))))
              .withColumn("status",       trim(col("status")))
              .withColumn("payment_mode", coalesce(upper(trim(col("payment_mode"))), lit("UNKNOWN")))
              .withColumn("order_value",
                  when(col("order_value") < 0, lit(None)).otherwise(col("order_value"))))

        # Derived time columns
        df = (df
              .withColumn("order_date",  col("order_ts").cast("date"))
              .withColumn("order_hour",  hour(col("order_ts")))
              .withColumn("time_slot",
                  when(col("order_hour").between(8,  11), "morning")
                  .when(col("order_hour").between(12, 15), "lunch")
                  .when(col("order_hour").between(16, 19), "evening")
                  .when(col("order_hour").between(20, 23), "dinner")
                  .otherwise("late_night"))
              .withColumn("day_of_week", dayofweek(col("order_ts")))
              .withColumn("is_weekend",  col("day_of_week").isin([1, 7])))

        # DQ flags
        df = (df
              .withColumn("_dq_has_null_customer",
                  col("customer_id").isNull())
              .withColumn("_dq_invalid_order_value",
                  col("order_value").isNull() | (col("order_value") <= 0))
              .withColumn("_dq_future_order",
                  col("order_ts") > current_timestamp()))
        return df

    def _aggregate_items(self, df: DataFrame) -> DataFrame:
        if "_corrupt_record" in df.columns:
            df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
        return (df.groupBy("order_id")
                  .agg(
                      count("item_id").alias("item_count"),
                      _round(_sum(col("quantity") * col("item_price")), 2).alias("items_subtotal")
                  ))

    def _aggregate_refunds(self, df: DataFrame) -> DataFrame:
        if "_corrupt_record" in df.columns:
            df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
        # Deduplicate
        w = Window.partitionBy("refund_id").orderBy(col("_ingested_at").desc())
        df = (df.withColumn("_rn", row_number().over(w))
                .filter(col("_rn") == 1)
                .drop("_rn"))
        return (df.groupBy("order_id")
                  .agg(
                      lit(True).alias("has_refund"),
                      _round(_sum("refund_amount"), 2).alias("refund_amount"),
                      first("refund_reason", ignorenulls=True).alias("refund_reason")
                  ))
