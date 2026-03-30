#!/bin/bash
# Sync notebooks to Databricks using CLI
# Usage: ./sync_to_databricks.sh

set -e

echo "🚀 Syncing notebooks to Databricks..."

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "❌ Databricks CLI not found. Install with:"
    echo "   pip install databricks-cli"
    exit 1
fi

# Check if configured
if ! databricks workspace ls / &> /dev/null; then
    echo "❌ Databricks CLI not configured. Run:"
    echo "   databricks configure --token"
    exit 1
fi

# Get user email for path
read -p "Enter your Databricks email: " USER_EMAIL

# Sync notebooks
echo "📤 Uploading notebooks..."
databricks workspace import_dir \
  ./databricks \
  "/Users/${USER_EMAIL}/databricks" \
  --overwrite

echo "✅ Sync complete!"
echo ""
echo "📍 Notebooks available at:"
echo "   /Users/${USER_EMAIL}/databricks/"
echo ""
echo "🔗 Open in Databricks:"
echo "   https://YOUR_WORKSPACE.cloud.databricks.com/#workspace/Users/${USER_EMAIL}/databricks"
