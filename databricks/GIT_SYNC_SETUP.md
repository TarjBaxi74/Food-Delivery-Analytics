# Git Sync Setup - Auto-Deploy to Databricks

## Option 1: Databricks Repos (Recommended) ⭐

This syncs your GitHub repo directly to Databricks - no manual uploads!

### Step 1: Push Code to GitHub

```bash
# In your local project
git add databricks/
git commit -m "Add Databricks notebooks"
git push origin main
```

### Step 2: Connect Repo to Databricks

1. In Databricks, click **Repos** (left sidebar)
2. Click **Add Repo**
3. Enter your GitHub URL: `https://github.com/YOUR_USERNAME/Food-Delivery-Operations-Analytics`
4. Click **Create Repo**

### Step 3: Access Your Notebooks

Your notebooks are now at:
```
/Repos/YOUR_USERNAME/Food-Delivery-Operations-Analytics/databricks/
```

### Step 4: Update Code

When you make changes locally:

```bash
# Make changes
git add .
git commit -m "Update notebooks"
git push

# In Databricks: Click "Pull" button in Repos
```

**That's it!** No re-uploading needed.

---

## Option 2: Databricks CLI (For Automation)

### Install Databricks CLI

```bash
pip install databricks-cli
```

### Configure Authentication

```bash
databricks configure --token
```

Enter:
- **Host**: `https://YOUR_WORKSPACE.cloud.databricks.com`
- **Token**: (Generate from User Settings → Developer → Access Tokens)

### Create Sync Script

Save this as `sync_to_databricks.sh`:

```bash
#!/bin/bash

# Sync notebooks to Databricks
databricks workspace import_dir \
  ./databricks \
  /Users/YOUR_EMAIL/databricks \
  --overwrite

echo "✓ Synced to Databricks!"
```

### Use It

```bash
chmod +x sync_to_databricks.sh
./sync_to_databricks.sh
```

---

## Option 3: Databricks Asset Bundles (DABs) - Advanced

For production deployments with CI/CD.

### Install Databricks CLI (v0.200+)

```bash
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
```

### Create Bundle Config

Save as `databricks.yml`:

```yaml
bundle:
  name: food-delivery-pipeline

workspace:
  host: https://YOUR_WORKSPACE.cloud.databricks.com

resources:
  jobs:
    daily_pipeline:
      name: Food Delivery Daily Pipeline
      tasks:
        - task_key: generate_data
          notebook_task:
            notebook_path: ./databricks/01_Data_Generation_Daily
        - task_key: bronze
          depends_on:
            - task_key: generate_data
          notebook_task:
            notebook_path: ./databricks/02_Bronze_Ingestion
        - task_key: silver
          depends_on:
            - task_key: bronze
          notebook_task:
            notebook_path: ./databricks/03_Silver_Transformation
        - task_key: analytics
          depends_on:
            - task_key: silver
          notebook_task:
            notebook_path: ./databricks/04_DBT_Models
      schedule:
        quartz_cron_expression: "0 0 2 * * ?"
        timezone_id: "UTC"
```

### Deploy

```bash
databricks bundle deploy
databricks bundle run daily_pipeline
```

---

## Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Repos** | ✅ Easy<br>✅ Git integration<br>✅ Version control | ❌ Manual pull | Learning, small teams |
| **CLI** | ✅ Automated<br>✅ Scriptable | ❌ Setup needed | Regular updates |
| **DABs** | ✅ Full CI/CD<br>✅ Job management | ❌ Complex setup | Production |

---

## Recommended Workflow

### For Development (Repos)

```bash
# 1. Make changes locally
vim databricks/01_Data_Generation_Daily.ipynb

# 2. Commit and push
git add .
git commit -m "Fix data generation"
git push

# 3. In Databricks: Click "Pull" in Repos
# 4. Run notebook
```

### For Production (CLI + GitHub Actions)

Create `.github/workflows/deploy-databricks.yml`:

```yaml
name: Deploy to Databricks

on:
  push:
    branches: [main]
    paths:
      - 'databricks/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Databricks CLI
        run: pip install databricks-cli
      
      - name: Deploy Notebooks
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          databricks workspace import_dir \
            ./databricks \
            /Users/${{ secrets.DATABRICKS_USER }}/databricks \
            --overwrite
```

Add secrets in GitHub:
- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`
- `DATABRICKS_USER`

Now every push auto-deploys! 🚀

---

## Quick Setup (Repos Method)

```bash
# 1. Push to GitHub
git add databricks/
git commit -m "Add notebooks"
git push

# 2. In Databricks:
#    - Click Repos → Add Repo
#    - Enter GitHub URL
#    - Click Create

# 3. Access notebooks at:
#    /Repos/YOUR_USERNAME/YOUR_REPO/databricks/

# 4. To update:
#    - Make changes locally
#    - git push
#    - Click "Pull" in Databricks Repos
```

---

## Testing Locally Before Deploy

Create `test_notebooks.py`:

```python
#!/usr/bin/env python3
"""Test notebooks locally before deploying"""

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import sys

def test_notebook(notebook_path):
    """Execute notebook and check for errors"""
    print(f"Testing {notebook_path}...")
    
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)
    
    # Skip cells with Databricks-specific code
    for cell in nb.cells:
        if 'dbutils' in cell.source or 'spark' in cell.source:
            cell.source = '# Skipped for local testing'
    
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    
    try:
        ep.preprocess(nb, {'metadata': {'path': './'}})
        print(f"✓ {notebook_path} passed")
        return True
    except Exception as e:
        print(f"✗ {notebook_path} failed: {e}")
        return False

if __name__ == "__main__":
    notebooks = [
        "databricks/01_Data_Generation_Daily.ipynb",
        # Add others as needed
    ]
    
    results = [test_notebook(nb) for nb in notebooks]
    
    if all(results):
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)
```

Run before pushing:
```bash
python test_notebooks.py
git push  # Only if tests pass
```

---

## My Recommendation

**Start with Repos** (easiest):
1. Push code to GitHub
2. Connect repo in Databricks
3. Click "Pull" when you update

**Later, add CLI** for automation:
1. Install databricks-cli
2. Create sync script
3. Run after each change

**Eventually, use GitHub Actions** for full CI/CD:
1. Auto-deploy on push
2. Run tests
3. Update jobs

---

## Files to Add

I'll create these for you:
- `sync_to_databricks.sh` - CLI sync script
- `databricks.yml` - Bundle config
- `.github/workflows/deploy-databricks.yml` - GitHub Actions
- `test_notebooks.py` - Local testing

Want me to create these files?
