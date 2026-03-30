# 🤖 Automation Guide - Deploy Without Manual Uploads

This guide shows you how to automatically deploy notebooks to Databricks without manually re-uploading files every time you make changes.

---

## 🎯 Goal

Stop manually uploading notebooks! Instead:
- Make changes locally
- Push to Git
- Auto-deploy to Databricks

---

## 🚀 Three Automation Options

### Option 1: Databricks Repos (Easiest) ⭐

**Setup Time**: 5 minutes  
**Best For**: Development, learning, small teams

#### How It Works
1. Push code to GitHub
2. Connect GitHub repo to Databricks
3. Click "Pull" to update notebooks

#### Setup Steps

**Step 1: Push to GitHub**
```bash
git add databricks/
git commit -m "Add Databricks notebooks"
git push origin main
```

**Step 2: Connect Repo in Databricks**
1. Open Databricks workspace
2. Click **Repos** (left sidebar)
3. Click **Add Repo**
4. Enter your GitHub URL:
   ```
   https://github.com/YOUR_USERNAME/Food-Delivery-Operations-Analytics
   ```
5. Click **Create Repo**

**Step 3: Access Notebooks**
Your notebooks are now at:
```
/Repos/YOUR_USERNAME/Food-Delivery-Operations-Analytics/databricks/
```

**Step 4: Update Code**
When you make changes:
```bash
# Make changes locally
vim databricks/01_Data_Generation_Daily.ipynb

# Push to GitHub
git add .
git commit -m "Update data generation"
git push

# In Databricks: Click "Pull" button in Repos
```

**✅ Done!** No more manual uploads.

---

### Option 2: Databricks CLI (Automated)

**Setup Time**: 10 minutes  
**Best For**: Regular updates, automation scripts

#### How It Works
1. Install Databricks CLI
2. Configure authentication
3. Run sync script to upload

#### Setup Steps

**Step 1: Install CLI**
```bash
pip install databricks-cli
```

**Step 2: Generate Access Token**
1. In Databricks: User Settings → Developer → Access Tokens
2. Click **Generate New Token**
3. Copy the token (save it securely!)

**Step 3: Configure CLI**
```bash
databricks configure --token
```

Enter:
- **Host**: `https://YOUR_WORKSPACE.cloud.databricks.com`
- **Token**: (paste the token you copied)

**Step 4: Test Connection**
```bash
databricks workspace ls /
```

Should list your workspace folders.

**Step 5: Use Sync Script**
```bash
# Make executable
chmod +x sync_to_databricks.sh

# Run sync
./sync_to_databricks.sh
```

Enter your Databricks email when prompted.

**✅ Done!** Notebooks uploaded automatically.

#### Daily Workflow
```bash
# 1. Make changes
vim databricks/01_Data_Generation_Daily.ipynb

# 2. Sync to Databricks
./sync_to_databricks.sh

# 3. Run notebook in Databricks
```

---

### Option 3: GitHub Actions (Full CI/CD)

**Setup Time**: 15 minutes  
**Best For**: Production, team collaboration, automated testing

#### How It Works
1. Configure GitHub secrets
2. Push to main branch
3. GitHub Actions auto-deploys to Databricks

#### Setup Steps

**Step 1: Generate Databricks Token**
1. In Databricks: User Settings → Developer → Access Tokens
2. Click **Generate New Token**
3. Copy the token

**Step 2: Add GitHub Secrets**
1. Go to your GitHub repo
2. Settings → Secrets and variables → Actions
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `DATABRICKS_HOST` | Your workspace URL | `https://dbc-abc123.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | Token from Step 1 | `dapi123abc...` |
| `DATABRICKS_USER` | Your email | `your.email@example.com` |

**Step 3: Verify Workflow File**
The workflow file is already created at:
```
.github/workflows/deploy-databricks.yml
```

**Step 4: Test Deployment**
```bash
# Make a change
vim databricks/01_Data_Generation_Daily.ipynb

# Commit and push
git add .
git commit -m "Update notebook"
git push origin main

# GitHub Actions will automatically deploy!
```

**Step 5: Monitor Deployment**
1. Go to GitHub repo → Actions tab
2. See deployment status
3. Check logs if needed

**✅ Done!** Every push auto-deploys!

#### Workflow Features
- ✅ Triggers on push to `main` branch
- ✅ Only runs when `databricks/` files change
- ✅ Can be manually triggered
- ✅ Shows deployment summary

---

## 📊 Comparison

| Feature | Repos | CLI | GitHub Actions |
|---------|-------|-----|----------------|
| **Setup Time** | 5 min | 10 min | 15 min |
| **Automation** | Manual pull | Script | Fully automatic |
| **Version Control** | ✅ Yes | ✅ Yes | ✅ Yes |
| **CI/CD** | ❌ No | ⚠️ Partial | ✅ Yes |
| **Team Friendly** | ✅ Yes | ⚠️ Partial | ✅ Yes |
| **Best For** | Learning | Regular updates | Production |

---

## 🎯 Recommended Approach

### For Learning / Solo Projects
**Use Databricks Repos**
- Easiest to set up
- Good version control
- Manual but simple

### For Regular Development
**Use Databricks CLI**
- Quick sync script
- Good for frequent updates
- More control

### For Production / Teams
**Use GitHub Actions**
- Fully automated
- Team collaboration
- CI/CD pipeline
- Professional workflow

---

## 🔄 Complete Workflow Example

### Using Repos (Recommended for Beginners)

```bash
# Day 1: Initial setup
git push origin main
# → Connect repo in Databricks

# Day 2: Update notebook
vim databricks/01_Data_Generation_Daily.ipynb
git add .
git commit -m "Increase order volume"
git push
# → Click "Pull" in Databricks Repos

# Day 3: Add new feature
vim databricks/06_New_Analysis.ipynb
git add .
git commit -m "Add new analysis"
git push
# → Click "Pull" in Databricks Repos
```

### Using GitHub Actions (Recommended for Teams)

```bash
# Day 1: Initial setup
# → Configure GitHub secrets (one time)

# Day 2: Update notebook
vim databricks/01_Data_Generation_Daily.ipynb
git add .
git commit -m "Increase order volume"
git push
# → Auto-deploys! Check Actions tab

# Day 3: Add new feature
vim databricks/06_New_Analysis.ipynb
git add .
git commit -m "Add new analysis"
git push
# → Auto-deploys! Check Actions tab
```

---

## 🧪 Testing Before Deploy

### Local Validation
```bash
# Test notebooks locally
python test_notebooks_locally.py

# Only push if tests pass
git push
```

### What It Checks
- ✅ Valid notebook structure
- ✅ No `sparkContext` usage
- ✅ No `include_groups` parameter
- ✅ No DBFS paths
- ✅ Required packages present

---

## 🐛 Troubleshooting

### Repos Issues

**Problem**: Can't find "Repos" in sidebar  
**Solution**: Use Databricks Community Edition (not AWS/Azure Databricks)

**Problem**: "Pull" button doesn't show changes  
**Solution**: Make sure you pushed to GitHub first

**Problem**: Notebooks not updating  
**Solution**: Click "Pull" button, then refresh page

### CLI Issues

**Problem**: `databricks: command not found`  
**Solution**: Install CLI: `pip install databricks-cli`

**Problem**: Authentication failed  
**Solution**: Regenerate token and run `databricks configure --token` again

**Problem**: Permission denied on sync script  
**Solution**: Run `chmod +x sync_to_databricks.sh`

### GitHub Actions Issues

**Problem**: Workflow not triggering  
**Solution**: Check that workflow file is in `.github/workflows/` folder

**Problem**: Authentication failed  
**Solution**: Verify GitHub secrets are set correctly

**Problem**: Deployment failed  
**Solution**: Check Actions tab for error logs

---

## 📝 Files Reference

### Automation Files
```
.
├── sync_to_databricks.sh              # CLI sync script
├── databricks.yml                     # Bundle config (advanced)
├── .github/workflows/
│   └── deploy-databricks.yml          # GitHub Actions workflow
├── test_notebooks_locally.py          # Local validation
└── databricks/
    ├── 01_Data_Generation_Daily.ipynb
    ├── 02_Bronze_Ingestion.ipynb
    ├── 03_Silver_Transformation.ipynb
    ├── 04_DBT_Models.ipynb
    └── 05_Pipeline_Orchestrator.ipynb
```

### Documentation Files
```
databricks/
├── QUICK_START.md              # 3-minute setup
├── DEPLOYMENT_STEPS.md         # Detailed deployment
├── GIT_SYNC_SETUP.md          # This guide (detailed)
├── CONTEXT_SUMMARY.md         # Complete overview
└── DEPLOYMENT_CHECKLIST.md    # Deployment checklist
```

---

## 🎓 Best Practices

1. **Always test locally first**
   ```bash
   python test_notebooks_locally.py
   ```

2. **Use meaningful commit messages**
   ```bash
   git commit -m "Fix SLA calculation in silver layer"
   ```

3. **Review changes before pushing**
   ```bash
   git diff
   git status
   ```

4. **Keep documentation updated**
   - Update README when adding features
   - Document configuration changes

5. **Use branches for experiments**
   ```bash
   git checkout -b experiment-new-metric
   # Make changes
   git push origin experiment-new-metric
   # Test in Databricks
   # Merge if successful
   ```

---

## 🚀 Next Steps

1. **Choose your automation method**
   - Repos for simplicity
   - CLI for control
   - GitHub Actions for automation

2. **Set it up** (5-15 minutes)
   - Follow setup steps above
   - Test with a small change

3. **Enjoy automated deployments!**
   - No more manual uploads
   - Version controlled
   - Team friendly

---

## 💡 Pro Tips

- **Repos**: Great for learning, easy to set up
- **CLI**: Perfect for quick iterations during development
- **GitHub Actions**: Best for production and team collaboration
- **Combine methods**: Use Repos for dev, GitHub Actions for prod

---

**Ready to automate?** Pick a method and follow the setup steps above!

**Questions?** Check `databricks/GIT_SYNC_SETUP.md` for more details.
