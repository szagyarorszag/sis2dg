#!/usr/bin/env python3
"""
Submission Verification Script
Checks if the project is ready for submission
"""

import os
import sys
from datetime import datetime

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✓" if exists else ("✗ MISSING" if required else "○")
    print(f"{status} {filepath}")
    return exists

def check_directory_exists(dirpath):
    """Check if a directory exists"""
    exists = os.path.exists(dirpath) and os.path.isdir(dirpath)
    status = "✓" if exists else "✗ MISSING"
    print(f"{status} {dirpath}/")
    return exists

def verify_submission():
    """Verify project is ready for submission"""
    
    print_header("DNS SHOP PIPELINE - SUBMISSION VERIFICATION")
    
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Deadline: December 4, 2025, 23:59:59\n")
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Required Files
    print_header("1. REQUIRED FILES")
    
    required_files = [
        'README.md',
        'requirements.txt',
        'create_schema.py',
        'src/scraper.py',
        'src/cleaner.py',
        'src/loader.py',
        'dags/dns_shop_dag.py',
    ]
    
    for filepath in required_files:
        if check_file_exists(filepath, required=True):
            checks_passed += 1
        total_checks += 1
    
    # Check 2: Optional but Recommended Files
    print_header("2. RECOMMENDED FILES")
    
    optional_files = [
        'test_pipeline.py',
        'setup.py',
        '.gitignore',
        'QUICK_REFERENCE.md',
        'DEFENSE_GUIDE.md',
        'src/__init__.py',
    ]
    
    for filepath in optional_files:
        check_file_exists(filepath, required=False)
    
    # Check 3: Directory Structure
    print_header("3. DIRECTORY STRUCTURE")
    
    required_dirs = ['src', 'dags', 'data', 'logs']
    
    for dirpath in required_dirs:
        if check_directory_exists(dirpath):
            checks_passed += 1
        total_checks += 1
    
    # Check 4: README Content
    print_header("4. README CONTENT")
    
    readme_sections = [
        'Project Overview',
        'website',
        'Installation',
        'Running',
        'Database Schema',
        'Airflow',
    ]
    
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read().lower()
        
        for section in readme_sections:
            if section.lower() in readme_content:
                print(f"✓ Contains '{section}' section")
                checks_passed += 1
            else:
                print(f"✗ Missing '{section}' section")
            total_checks += 1
    except:
        print("✗ Could not read README.md")
        total_checks += len(readme_sections)
    
    # Check 5: Code Quality
    print_header("5. CODE QUALITY CHECKS")
    
    # Check imports
    try:
        sys.path.insert(0, 'src')
        from scraper import DNSShopScraper
        from cleaner import DataCleaner
        from loader import DatabaseLoader
        print("✓ All modules can be imported")
        checks_passed += 1
    except Exception as e:
        print(f"✗ Import error: {e}")
    total_checks += 1
    
    # Check DAG syntax
    try:
        with open('dags/dns_shop_dag.py', 'r') as f:
            dag_content = f.read()
            if 'schedule_interval' in dag_content:
                print("✓ DAG has schedule_interval defined")
                checks_passed += 1
            else:
                print("✗ DAG missing schedule_interval")
            total_checks += 1
            
            if 'retries' in dag_content:
                print("✓ DAG has retry logic")
                checks_passed += 1
            else:
                print("✗ DAG missing retry logic")
            total_checks += 1
    except:
        print("✗ Could not read DAG file")
        total_checks += 2
    
    # Check 6: Data Files (optional but good to have)
    print_header("6. DATA FILES (Optional)")
    
    data_files = [
        'data/raw_products.json',
        'data/cleaned_products.csv',
        'data/output.db',
    ]
    
    for filepath in data_files:
        check_file_exists(filepath, required=False)
    
    # Check 7: Git Repository
    print_header("7. GIT REPOSITORY")
    
    if os.path.exists('.git'):
        print("✓ Git repository initialized")
        
        # Check for recent commits
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%cd', '--date=iso'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                last_commit = result.stdout.strip()
                print(f"✓ Last commit: {last_commit}")
                
                # Parse commit date
                commit_date = datetime.fromisoformat(last_commit.split()[0])
                deadline = datetime(2025, 12, 4, 23, 59, 59)
                
                if commit_date <= deadline:
                    print("✓ Last commit is before deadline")
                    checks_passed += 1
                else:
                    print("✗ Last commit is AFTER deadline!")
                total_checks += 1
        except:
            print("○ Could not check commit dates")
    else:
        print("⚠️  Not a git repository")
        print("   Initialize with: git init")
    
    # Final Summary
    print_header("SUBMISSION VERIFICATION SUMMARY")
    
    print(f"Checks passed: {checks_passed}/{total_checks}")
    print(f"Success rate: {(checks_passed/total_checks*100):.1f}%\n")
    
    if checks_passed >= total_checks * 0.8:
        print("✓ PROJECT IS READY FOR SUBMISSION!")
        print("\nNext steps:")
        print("1. Commit all changes: git add . && git commit -m 'Final submission'")
        print("2. Push to GitHub: git push origin main")
        print("3. Verify GitHub repo is accessible")
        print("4. Run test_pipeline.py one final time")
        print("5. Prepare for defense on December 5")
        return True
    else:
        print("✗ PROJECT NEEDS ATTENTION!")
        print("\nIssues to fix:")
        print("1. Check all required files are present")
        print("2. Complete README documentation")
        print("3. Verify code can be imported")
        print("4. Test the complete pipeline")
        return False

def main():
    """Main function"""
    try:
        success = verify_submission()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
