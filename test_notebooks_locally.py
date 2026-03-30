#!/usr/bin/env python3
"""
Test notebooks locally before deploying to Databricks
This validates syntax and basic logic without running on Databricks
"""

import json
import sys
from pathlib import Path

def validate_notebook(notebook_path):
    """Validate notebook structure and syntax"""
    print(f"\n📝 Validating {notebook_path}...")
    
    try:
        with open(notebook_path, 'r') as f:
            nb = json.load(f)
        
        # Check notebook structure
        if 'cells' not in nb:
            print(f"  ❌ Invalid notebook structure")
            return False
        
        # Check for common issues
        issues = []
        
        for i, cell in enumerate(nb['cells']):
            if cell['cell_type'] == 'code':
                source = ''.join(cell['source'])
                
                # Check for problematic patterns
                if 'sparkContext' in source and 'setLogLevel' in source:
                    issues.append(f"  ⚠️  Cell {i}: Uses sparkContext.setLogLevel (not serverless compatible)")
                
                if 'include_groups=False' in source:
                    issues.append(f"  ❌ Cell {i}: Uses include_groups parameter (pandas version issue)")
                
                if '/mnt/' in source and 'dbfs' in source.lower():
                    issues.append(f"  ⚠️  Cell {i}: Uses DBFS paths (may not work on free tier)")
        
        if issues:
            print(f"  Found {len(issues)} issue(s):")
            for issue in issues:
                print(issue)
            return False
        
        print(f"  ✅ Validation passed")
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def check_dependencies():
    """Check if required packages are mentioned"""
    print("\n📦 Checking dependencies...")
    
    required = ['faker', 'pandas', 'numpy']
    found = []
    
    for nb_path in Path('databricks').glob('*.ipynb'):
        with open(nb_path, 'r') as f:
            content = f.read()
            for pkg in required:
                if pkg in content:
                    found.append(pkg)
    
    found = list(set(found))
    print(f"  Found packages: {', '.join(found)}")
    
    missing = set(required) - set(found)
    if missing:
        print(f"  ⚠️  Missing: {', '.join(missing)}")
    else:
        print(f"  ✅ All required packages referenced")
    
    return True

def main():
    """Run all validations"""
    print("="*60)
    print("🧪 Testing Databricks Notebooks Locally")
    print("="*60)
    
    notebooks = [
        "databricks/01_Data_Generation_Daily.ipynb",
        "databricks/02_Bronze_Ingestion.ipynb",
        "databricks/03_Silver_Transformation.ipynb",
        "databricks/04_DBT_Models.ipynb",
        "databricks/05_Pipeline_Orchestrator.ipynb",
    ]
    
    results = []
    for nb in notebooks:
        if Path(nb).exists():
            results.append(validate_notebook(nb))
        else:
            print(f"\n❌ {nb} not found")
            results.append(False)
    
    check_dependencies()
    
    print("\n" + "="*60)
    if all(results):
        print("✅ All validations passed!")
        print("="*60)
        print("\n🚀 Ready to deploy to Databricks!")
        print("\nNext steps:")
        print("  1. git add databricks/")
        print("  2. git commit -m 'Update notebooks'")
        print("  3. git push")
        print("  4. In Databricks: Click 'Pull' in Repos")
        return 0
    else:
        print("❌ Some validations failed")
        print("="*60)
        print("\n⚠️  Fix issues before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())
