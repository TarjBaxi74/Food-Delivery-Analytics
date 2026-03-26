import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyspark.sql import SparkSession
from config.settings import PATHS
from src.spark_jobs.bronze.ingest_raw import BronzeIngestion
from src.spark_jobs.silver.build_order_facts import OrderFactsBuilder
from src.spark_jobs.silver.build_delivery_ops import DeliveryOpsBuilder
from src.spark_jobs.silver.build_restaurant_support import RestaurantSupportBuilder
from src.spark_jobs.common.quality_checks import get_dq_summary, print_dq_report


def create_spark_session() -> SparkSession:
    return (SparkSession.builder
        .appName("FoodDeliveryPipeline")
        .master("local[*]")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "4g")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate())


def run_pipeline():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    bronze_path = str(PATHS["bronze"])
    silver_path = str(PATHS["silver"])

    try:
        # ── Bronze ────────────────────────────────────────────────────────────
        print("=" * 60)
        print("BRONZE LAYER - Ingesting raw files")
        print("=" * 60)
        bronze = BronzeIngestion(spark=spark,
                                 raw_path=str(PATHS["raw"]),
                                 bronze_path=bronze_path)
        bronze.run_all()

        # ── Silver ────────────────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("SILVER LAYER - 3 joined tables")
        print("=" * 60)

        # 1. order_facts = orders + order_items (agg) + refunds
        order_facts = OrderFactsBuilder(spark, bronze_path, silver_path)
        df_orders = order_facts.build()
        order_facts.write(df_orders)
        dq = get_dq_summary(df_orders, ["_dq_has_null_customer",
                                         "_dq_invalid_order_value",
                                         "_dq_future_order"])
        print_dq_report("order_facts", dq)

        # 2. delivery_ops = delivery_events + riders
        delivery_ops = DeliveryOpsBuilder(spark, bronze_path, silver_path)
        df_delivery = delivery_ops.build()
        delivery_ops.write(df_delivery)
        dq = get_dq_summary(df_delivery, ["_dq_orphan_order",
                                           "_dq_invalid_event",
                                           "_dq_missing_rider"])
        print_dq_report("delivery_ops", dq)

        # 3. restaurant_support = restaurants + support_tickets (via orders)
        restaurant_support = RestaurantSupportBuilder(spark, bronze_path, silver_path)
        df_rest = restaurant_support.build()
        restaurant_support.write(df_rest)

        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)

    finally:
        spark.stop()


if __name__ == "__main__":
    run_pipeline()
