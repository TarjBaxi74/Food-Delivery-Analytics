"""
Silver: restaurant_support
============================
Joins restaurants + support_tickets (enriched via orders → restaurant_id).

Support tickets only have order_id; this builder walks the join chain
support_tickets → orders → restaurants so every ticket row carries
full restaurant context for analysis.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window


class RestaurantSupportBuilder:
    def __init__(self, spark: SparkSession, bronze_path: str, silver_path: str):
        self.spark = spark
        self.bronze_path = bronze_path
        self.silver_path = silver_path

    def build(self) -> DataFrame:
        restaurants = self._clean_restaurants(self._read("restaurants"))
        tickets     = self._clean_tickets(self._read("support_tickets"))

        # Walk: tickets → orders to get restaurant_id + city
        orders_slim = (self._read("orders")
                       .select("order_id",
                               col("restaurant_id").alias("order_restaurant_id"),
                               col("city").alias("order_city")))

        tickets_enriched = tickets.join(orders_slim, on="order_id", how="left")

        # Now join with restaurants dimension
        df = tickets_enriched.join(
            restaurants.select("restaurant_id", "cuisine_type", "rating_band", "onboarding_date"),
            tickets_enriched["order_restaurant_id"] == restaurants["restaurant_id"],
            how="left"
        ).drop("order_restaurant_id")

        return df

    def write(self, df: DataFrame) -> None:
        (df.write.mode("overwrite")
           .parquet(f"{self.silver_path}/restaurant_support"))
        print(f"  Silver restaurant_support written ({df.count()} rows)")

    # ── private helpers ───────────────────────────────────────────────────────

    def _read(self, table: str) -> DataFrame:
        return self.spark.read.parquet(f"{self.bronze_path}/{table}")

    def _clean_restaurants(self, df: DataFrame) -> DataFrame:
        if "_corrupt_record" in df.columns:
            df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
        w = Window.partitionBy("restaurant_id").orderBy(col("_ingested_at").desc())
        return (df.withColumn("_rn", row_number().over(w))
                  .filter(col("_rn") == 1)
                  .drop("_rn"))

    def _clean_tickets(self, df: DataFrame) -> DataFrame:
        if "_corrupt_record" in df.columns:
            df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")
        w = Window.partitionBy("ticket_id").orderBy(col("_ingested_at").desc())
        return (df.withColumn("_rn", row_number().over(w))
                  .filter(col("_rn") == 1)
                  .drop("_rn"))
