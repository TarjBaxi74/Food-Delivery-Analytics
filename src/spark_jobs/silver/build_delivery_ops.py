"""
Silver: delivery_ops
======================
Joins delivery_events + riders into one enriched event stream.

Each event row gains rider context (city, shift_type, joining_date)
so analysts never need to look up rider metadata separately.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit, row_number
from pyspark.sql.window import Window


VALID_EVENT_TYPES = [
    "order_confirmed", "restaurant_accepted", "food_prep_started",
    "food_ready", "rider_assigned", "rider_picked_up",
    "out_for_delivery", "delivered", "delivery_failed", "cancelled",
]


class DeliveryOpsBuilder:
    def __init__(self, spark: SparkSession, bronze_path: str, silver_path: str):
        self.spark = spark
        self.bronze_path = bronze_path
        self.silver_path = silver_path

    def build(self) -> DataFrame:
        events = self._clean_events(self._read("delivery_events"))
        riders = self._clean_riders(self._read("riders"))

        # Enrich events with rider metadata
        df = events.join(
            riders.select("rider_id",
                          col("city").alias("rider_city"),
                          col("shift_type").alias("rider_shift"),
                          "joining_date"),
            on="rider_id", how="left"
        )

        # DQ flags — use a broadcast join instead of collect() to avoid worker version mismatch
        order_ids_df = self._read("orders").select("order_id").distinct()
        df = (df
              .join(order_ids_df.withColumnRenamed("order_id", "_valid_order_id"),
                    df["order_id"] == col("_valid_order_id"), how="left")
              .withColumn("_dq_orphan_order",   col("_valid_order_id").isNull())
              .drop("_valid_order_id")
              .withColumn("_dq_invalid_event",  ~col("event_type").isin(VALID_EVENT_TYPES))
              .withColumn("_dq_missing_rider",
                  col("event_type").isin(["rider_assigned", "rider_picked_up",
                                          "out_for_delivery", "delivered"])
                  & col("rider_id").isNull()))
        return df

    def write(self, df: DataFrame) -> None:
        (df.write.mode("overwrite")
           .parquet(f"{self.silver_path}/delivery_ops"))
        print(f"  Silver delivery_ops written ({df.count()} rows)")

    # ── private helpers ───────────────────────────────────────────────────────

    def _read(self, table: str) -> DataFrame:
        return self.spark.read.parquet(f"{self.bronze_path}/{table}")

    def _clean_events(self, df: DataFrame) -> DataFrame:
        if "_corrupt_record" in df.columns:
            df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
        # Deduplicate: one event per (order_id, event_type)
        w = Window.partitionBy("order_id", "event_type").orderBy(col("_ingested_at").desc())
        return (df.withColumn("_rn", row_number().over(w))
                  .filter(col("_rn") == 1)
                  .drop("_rn"))

    def _clean_riders(self, df: DataFrame) -> DataFrame:
        if "_corrupt_record" in df.columns:
            df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
        w = Window.partitionBy("rider_id").orderBy(col("_ingested_at").desc())
        return (df.withColumn("_rn", row_number().over(w))
                  .filter(col("_rn") == 1)
                  .drop("_rn"))
