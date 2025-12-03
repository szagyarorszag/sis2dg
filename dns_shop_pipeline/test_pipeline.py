"""
Test Script for DNS Shop Pipeline
Runs a complete test of the entire pipeline
"""

import sys
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import DNSShopScraper
from cleaner import DataCleaner
from loader import DatabaseLoader


def print_separator(title):
    """Print formatted section separator"""
    logger.info("\n" + "="*70)
    logger.info(f"  {title}")
    logger.info("="*70 + "\n")


def test_pipeline():
    """Test complete pipeline execution"""
    
    print_separator("DNS SHOP PIPELINE - FULL TEST")
    
    start_time = datetime.now()
    
    # File paths
    raw_file = 'data/raw_products.json'
    cleaned_file = 'data/cleaned_products.csv'
    db_file = 'data/output.db'
    
    try:
        # STEP 1: Scraping
        print_separator("STEP 1: WEB SCRAPING")
        logger.info("Starting web scraper...")
        
        scraper = DNSShopScraper(headless=True)
        products = scraper.scrape(max_products=120)
        
        if not products:
            logger.error("❌ No products scraped!")
            return False
        
        scraper.save_to_json(raw_file)
        logger.info(f"✓ Scraped {len(products)} products")
        logger.info(f"✓ Saved to {raw_file}")
        
        # STEP 2: Cleaning
        print_separator("STEP 2: DATA CLEANING")
        logger.info("Starting data cleaner...")
        
        cleaner = DataCleaner(raw_file)
        cleaned_data = cleaner.clean()
        
        if cleaned_data is None or len(cleaned_data) == 0:
            logger.error("❌ No data after cleaning!")
            return False
        
        cleaner.save_to_csv(cleaned_file)
        stats = cleaner.get_summary_statistics()
        
        logger.info(f"✓ Cleaned {len(cleaned_data)} records")
        logger.info(f"✓ Saved to {cleaned_file}")
        logger.info("\nCleaning Statistics:")
        logger.info(f"  Total records: {stats['total_records']}")
        logger.info(f"  Average price: {stats['avg_price']:.2f} KZT")
        logger.info(f"  Price range: {stats['min_price']:.0f} - {stats['max_price']:.0f} KZT")
        logger.info(f"  Average rating: {stats['avg_rating']:.2f}")
        logger.info(f"  Products with discount: {stats['products_with_discount']}")
        
        if len(cleaned_data) < 100:
            logger.warning(f"⚠️  Warning: Only {len(cleaned_data)} records (minimum is 100)")
        
        # STEP 3: Loading
        print_separator("STEP 3: DATABASE LOADING")
        logger.info("Starting database loader...")
        
        loader = DatabaseLoader(db_file)
        
        if not loader.connect():
            logger.error("❌ Failed to connect to database!")
            return False
        
        loader.create_table()
        loader.create_indexes()
        
        if not loader.load_data(cleaned_file):
            logger.error("❌ Failed to load data!")
            return False
        
        loader.cleanup_duplicates()
        
        db_stats = loader.get_statistics()
        logger.info(f"✓ Data loaded successfully")
        logger.info(f"✓ Database: {db_file}")
        logger.info("\nDatabase Statistics:")
        logger.info(f"  Total products: {db_stats['total_products']}")
        logger.info(f"  Average price: {db_stats['avg_price']:.2f} KZT")
        logger.info(f"  Price range: {db_stats['min_price']:.0f} - {db_stats['max_price']:.0f} KZT")
        logger.info(f"  Average rating: {db_stats['avg_rating']:.2f}")
        logger.info(f"  By category: {db_stats['by_category']}")
        
        logger.info("\nLatest 5 records:")
        latest = loader.get_latest_records(5)
        for idx, record in enumerate(latest, 1):
            logger.info(f"  {idx}. {record[0][:50]}... - {record[1]:.0f} KZT")
        
        loader.close()
        
        # STEP 4: Summary
        print_separator("PIPELINE EXECUTION SUMMARY")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✓ Pipeline completed successfully!")
        logger.info(f"\nExecution Summary:")
        logger.info(f"  Scraped: {len(products)} records")
        logger.info(f"  Cleaned: {len(cleaned_data)} records")
        logger.info(f"  Loaded: {db_stats['total_products']} records")
        logger.info(f"  Data quality: {(len(cleaned_data)/len(products)*100):.1f}% retention")
        logger.info(f"  Execution time: {duration:.1f} seconds")
        logger.info(f"  Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Validation checks
        print_separator("VALIDATION CHECKS")
        
        checks_passed = 0
        total_checks = 5
        
        # Check 1: Minimum records
        if len(cleaned_data) >= 100:
            logger.info("✓ Check 1: Minimum 100 records after cleaning - PASSED")
            checks_passed += 1
        else:
            logger.warning("✗ Check 1: Minimum 100 records after cleaning - FAILED")
        
        # Check 2: Database created
        if os.path.exists(db_file):
            logger.info("✓ Check 2: Database file created - PASSED")
            checks_passed += 1
        else:
            logger.warning("✗ Check 2: Database file created - FAILED")
        
        # Check 3: Data files exist
        if os.path.exists(raw_file) and os.path.exists(cleaned_file):
            logger.info("✓ Check 3: All data files created - PASSED")
            checks_passed += 1
        else:
            logger.warning("✗ Check 3: All data files created - FAILED")
        
        # Check 4: Price data valid
        if stats['avg_price'] > 0 and stats['min_price'] > 0:
            logger.info("✓ Check 4: Price data is valid - PASSED")
            checks_passed += 1
        else:
            logger.warning("✗ Check 4: Price data is valid - FAILED")
        
        # Check 5: Database has records
        if db_stats['total_products'] > 0:
            logger.info("✓ Check 5: Database contains records - PASSED")
            checks_passed += 1
        else:
            logger.warning("✗ Check 5: Database contains records - FAILED")
        
        logger.info(f"\nValidation Result: {checks_passed}/{total_checks} checks passed")
        
        if checks_passed == total_checks:
            print_separator("✓ ALL TESTS PASSED - PIPELINE READY FOR SUBMISSION")
            return True
        else:
            print_separator("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
            return False
        
    except Exception as e:
        logger.error(f"\n❌ Pipeline test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
