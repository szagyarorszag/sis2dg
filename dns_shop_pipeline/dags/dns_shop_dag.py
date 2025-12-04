from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraper import DNSShopScraper
from cleaner import DataCleaner
from loader import DatabaseLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DATA_FILE = os.path.join(BASE_DIR, 'data', 'raw_products.json')
CLEANED_DATA_FILE = os.path.join(BASE_DIR, 'data', 'cleaned_products.csv')
DATABASE_FILE = os.path.join(BASE_DIR, 'data', 'output.db')

default_args = {
    'owner': 'daniil',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}


def scrape_task(**context):

    logger.info("TASK 1: Starting web scraping")
    
    try:
        scraper = DNSShopScraper(headless=True)
        products = scraper.scrape(max_products=150)
        
        if not products:
            raise Exception("No products scraped from website")
        
        # Save to JSON
        scraper.save_to_json(RAW_DATA_FILE)
        
        logger.info(f"Successfully scraped {len(products)} products")
        logger.info(f"Data saved to: {RAW_DATA_FILE}")
        
        # Push data count to XCom for monitoring
        context['ti'].xcom_push(key='scraped_count', value=len(products))
        
        logger.info("TASK 1: Completed successfully")
        return len(products)
        
    except Exception as e:
        logger.error(f"TASK 1: Failed with error: {str(e)}")
        raise


def clean_task(**context):

    logger.info("TASK 2: Starting data cleaning")
    
    try:
        # Get scraped count from previous task
        scraped_count = context['ti'].xcom_pull(key='scraped_count', task_ids='scrape_data')
        logger.info(f"Received {scraped_count} records from scraping task")
        
        cleaner = DataCleaner(RAW_DATA_FILE)
        cleaned_data = cleaner.clean()
        
        if cleaned_data is None or len(cleaned_data) == 0:
            raise Exception("No data after cleaning")
        
        if len(cleaned_data) < 100:
            logger.warning(f"Only {len(cleaned_data)} records after cleaning (minimum is 100)")
        
        # Save cleaned data
        cleaner.save_to_csv(CLEANED_DATA_FILE)
        
        # Get statistics
        stats = cleaner.get_summary_statistics()
        logger.info(f"Cleaning statistics: {stats}")
        
        logger.info(f"Successfully cleaned {len(cleaned_data)} records")
        logger.info(f"Data saved to: {CLEANED_DATA_FILE}")
        
        # Push data count to XCom
        context['ti'].xcom_push(key='cleaned_count', value=len(cleaned_data))
        
        logger.info("TASK 2: Completed successfully")
        return len(cleaned_data)
        
    except Exception as e:
        logger.error(f"TASK 2: Failed with error: {str(e)}")
        raise


def load_task(**context):
    logger.info("TASK 3: Starting database loading")
    
    try:
        cleaned_count = context['ti'].xcom_pull(key='cleaned_count', task_ids='clean_data')
        logger.info(f"Received {cleaned_count} records from cleaning task")
        
        loader = DatabaseLoader(DATABASE_FILE)
        
        if not loader.connect():
            raise Exception("Failed to connect to database")
        
        loader.create_table()
        loader.create_indexes()
        
        if not loader.load_data(CLEANED_DATA_FILE):
            raise Exception("Failed to load data into database")
        
        loader.cleanup_duplicates()
        
        stats = loader.get_statistics()
        logger.info(f"Database statistics: {stats}")
        
        latest = loader.get_latest_records(5)
        logger.info("Latest 5 records loaded:")
        for idx, record in enumerate(latest, 1):
            logger.info(f"  {idx}. {record[0][:50]} - {record[1]} KZT")
        
        total_records = stats.get('total_products', 0)
        logger.info(f"Total records in database: {total_records}")
        
        loader.close()
        
        context['ti'].xcom_push(key='loaded_count', value=total_records)
        
        logger.info("TASK 3: Completed successfully")
        return total_records
        
    except Exception as e:
        logger.error(f"TASK 3: Failed with error: {str(e)}")
        raise


def summary_task(**context):
    logger.info("PIPELINE EXECUTION SUMMARY")
    
    try:
        scraped = context['ti'].xcom_pull(key='scraped_count', task_ids='scrape_data')
        cleaned = context['ti'].xcom_pull(key='cleaned_count', task_ids='clean_data')
        loaded = context['ti'].xcom_pull(key='loaded_count', task_ids='load_data')
        
        logger.info(f"Scraped records: {scraped}")
        logger.info(f"Cleaned records: {cleaned}")
        logger.info(f"Total in database: {loaded}")
        logger.info(f"Data quality: {(cleaned/scraped*100):.1f}% records retained after cleaning")
        
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        
        return {
            'scraped': scraped,
            'cleaned': cleaned,
            'loaded': loaded,
            'execution_date': context['execution_date'].isoformat()
        }
        
    except Exception as e:
        logger.error(f"Summary task failed: {str(e)}")
        raise

dag = DAG(
    'dns_shop_tv_pipeline',
    default_args=default_args,
    description='Daily pipeline to scrape, clean, and load DNS Shop TV product data with pagination',
    schedule_interval='0 2 * * *',
    catchup=False,
    tags=['scraping', 'dns-shop', 'etl', 'tvs', 'pagination'],
)

scrape = PythonOperator(
    task_id='scrape_data',
    python_callable=scrape_task,
    provide_context=True,
    dag=dag,
)

clean = PythonOperator(
    task_id='clean_data',
    python_callable=clean_task,
    provide_context=True,
    dag=dag,
)

load = PythonOperator(
    task_id='load_data',
    python_callable=load_task,
    provide_context=True,
    dag=dag,
)

summary = PythonOperator(
    task_id='pipeline_summary',
    python_callable=summary_task,
    provide_context=True,
    dag=dag,
)

scrape >> clean >> load >> summary