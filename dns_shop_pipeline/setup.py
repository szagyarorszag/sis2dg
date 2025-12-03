#!/usr/bin/env python3
"""
Setup Script for DNS Shop Pipeline
Initializes project structure and dependencies
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("Python 3.8+ is required")
        return False
    logger.info(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def create_directories():
    """Create necessary directories"""
    directories = ['data', 'logs', 'dags']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"✓ Created/verified directory: {directory}/")
    
    return True


def install_dependencies():
    """Install Python dependencies"""
    logger.info("Installing dependencies from requirements.txt...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        logger.info("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False


def check_chrome():
    """Check if Chrome/Chromium is available"""
    try:
        result = subprocess.run(['which', 'chromium'], capture_output=True)
        if result.returncode == 0:
            logger.info("✓ Chromium browser found")
            return True
        
        result = subprocess.run(['which', 'google-chrome'], capture_output=True)
        if result.returncode == 0:
            logger.info("✓ Chrome browser found")
            return True
        
        logger.warning("⚠️  Chrome/Chromium not found - required for scraping")
        logger.info("Install with: sudo apt-get install chromium-browser")
        return False
    except:
        logger.warning("⚠️  Could not check for Chrome/Chromium")
        return False


def initialize_database():
    """Initialize database schema"""
    logger.info("Initializing database schema...")
    
    try:
        subprocess.check_call([sys.executable, 'create_schema.py'])
        logger.info("✓ Database schema created")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create database schema: {e}")
        return False


def setup_airflow():
    """Setup Airflow"""
    logger.info("Setting up Airflow...")
    
    airflow_home = os.getcwd()
    os.environ['AIRFLOW_HOME'] = airflow_home
    
    logger.info(f"AIRFLOW_HOME set to: {airflow_home}")
    
    try:
        # Initialize Airflow database
        logger.info("Initializing Airflow database...")
        subprocess.check_call(['airflow', 'db', 'init'])
        
        logger.info("✓ Airflow database initialized")
        logger.info("\nTo create Airflow admin user, run:")
        logger.info("  airflow users create \\")
        logger.info("    --username admin \\")
        logger.info("    --firstname Admin \\")
        logger.info("    --lastname User \\")
        logger.info("    --role Admin \\")
        logger.info("    --email admin@example.com \\")
        logger.info("    --password admin")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup Airflow: {e}")
        return False
    except FileNotFoundError:
        logger.warning("⚠️  Airflow not found - install dependencies first")
        return False


def print_next_steps():
    """Print next steps for user"""
    logger.info("\n" + "="*70)
    logger.info("SETUP COMPLETE - NEXT STEPS")
    logger.info("="*70)
    logger.info("\n1. Test the pipeline:")
    logger.info("   python test_pipeline.py")
    logger.info("\n2. Create Airflow admin user (if not done):")
    logger.info("   airflow users create --username admin --password admin \\")
    logger.info("     --firstname Admin --lastname User --role Admin \\")
    logger.info("     --email admin@example.com")
    logger.info("\n3. Start Airflow scheduler (Terminal 1):")
    logger.info("   export AIRFLOW_HOME=$(pwd)")
    logger.info("   airflow scheduler")
    logger.info("\n4. Start Airflow web server (Terminal 2):")
    logger.info("   export AIRFLOW_HOME=$(pwd)")
    logger.info("   airflow webserver --port 8080")
    logger.info("\n5. Access Airflow UI:")
    logger.info("   http://localhost:8080")
    logger.info("\n6. Enable and trigger the DAG:")
    logger.info("   - Find 'dns_shop_pipeline' in the UI")
    logger.info("   - Toggle it ON")
    logger.info("   - Click play button to trigger manually")
    logger.info("\n" + "="*70 + "\n")


def main():
    """Main setup function"""
    logger.info("="*70)
    logger.info("DNS SHOP PIPELINE - SETUP SCRIPT")
    logger.info("="*70 + "\n")
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Creating directories", create_directories),
        ("Installing dependencies", install_dependencies),
        ("Checking Chrome/Chromium", check_chrome),
        ("Initializing database", initialize_database),
        ("Setting up Airflow", setup_airflow),
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n[{step_name}]")
        if not step_func():
            logger.error(f"Setup failed at: {step_name}")
            return False
    
    print_next_steps()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
