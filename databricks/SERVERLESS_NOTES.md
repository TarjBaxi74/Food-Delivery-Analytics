# Databricks Serverless Compute Notes

## What is Serverless Compute?

Databricks Serverless is a **managed compute option** that:
- ✅ Starts instantly (no cluster startup wait)
- ✅ Auto-scales based on workload
- ✅ No cluster management needed
- ✅ Pay only for what you use
- ✅ Perfect for Free Edition

## Limitations

Serverless compute has some restrictions:
- ❌ No direct JVM access (`sparkContext` not available)
- ❌ Cannot set log levels programmatically
- ❌ Some advanced Spark configurations unavailable

## What We Fixed

All notebooks have been updated to work with serverless:

### Removed:
```python
# OLD (doesn't work on serverless)
spark.sparkContext.setLogLevel("WARN")
```

### Replaced with:
```python
# NEW (serverless compatible)
# Note: setLogLevel not available on serverless compute
```

## How to Use Serverless

1. **Open any notebook**
2. **Click the compute dropdown** (top right)
3. **Select "Serverless"**
4. **Run your notebook**

That's it! No cluster creation needed.

## When to Use Regular Cluster vs Serverless

| Use Case | Recommendation |
|----------|----------------|
| Learning/Testing | ✅ Serverless |
| Small datasets (<10GB) | ✅ Serverless |
| Infrequent runs | ✅ Serverless |
| Need JVM access | ❌ Use regular cluster |
| Custom Spark configs | ❌ Use regular cluster |
| Large datasets (>100GB) | ❌ Use regular cluster |

## For This Project

**Serverless is perfect!** Our pipeline:
- Generates ~1000 orders/day
- Processes <1GB of data
- Runs in minutes
- No special configs needed

## Compatibility

All 5 notebooks are **100% serverless compatible**:
- ✅ 01_Data_Generation_Daily.ipynb
- ✅ 02_Bronze_Ingestion.ipynb
- ✅ 03_Silver_Transformation.ipynb
- ✅ 04_DBT_Models.ipynb
- ✅ 05_Pipeline_Orchestrator.ipynb

## Cost

Serverless on Free Edition:
- **Free tier**: Limited compute hours/month
- **After free tier**: Pay per DBU (Databricks Unit)
- **This project**: Should stay within free tier for daily runs

## References

- [Databricks Serverless Docs](https://docs.databricks.com/serverless-compute/index.html)
- [Serverless Limitations](https://docs.databricks.com/release-notes/serverless.html#limitations)
