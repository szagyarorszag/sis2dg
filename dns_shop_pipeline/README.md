# DNS Shop Kazakhstan - Data Pipeline Project

## Project Overview

This project implements a complete ETL (Extract, Transform, Load) data pipeline that scrapes product data from **dns-shop.kz** (a dynamic e-commerce website), cleans and preprocesses the data, and loads it into a SQLite database. The entire workflow is automated using Apache Airflow.

**Website:** https://dns-shop.kz/ (Category: Televisions/Телевизоры)

## Why DNS Shop Kazakhstan?

DNS Shop is a major electronics retailer in Kazakhstan(actually Russian) with a dynamic website that:
- Uses JavaScript rendering for product listings
- Implements infinite scroll for loading products
- Contains rich product data (prices, ratings, availability)
- Requires Selenium for proper data extraction

## Project Structure

```
dns_shop_pipeline/
│
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── create_schema.py          # Database schema creation script
│
├── src/
│   ├── scraper.py           # Web scraping module (Selenium)
│   ├── cleaner.py           # Data cleaning and preprocessing
│   └── loader.py            # SQLite database loader
│
├── dags/
│   └── dns_shop_dag.py      # Airflow DAG definition
│
├── data/
│   ├── raw_products.json    # Raw scraped data
│   ├── cleaned_products.csv # Cleaned data
│   └── output.db            # SQLite database
│
└── logs/                     # Airflow logs directory
```

## Features

### 1. Web Scraping (scraper.py)
- Uses Selenium WebDriver for dynamic content
- Handles city selection modal ("Все верно")
- Navigates to TV category automatically
- Implements pagination to scrape multiple pages (150+ products)
- Extracts comprehensive product information:
  - Product name and ID
  - Current price and old price (if discounted)
  - Rating and availability
  - Product URL
  - Scraping timestamp

### 2. Data Cleaning (cleaner.py)
- Removes duplicate records
- Handles missing values intelligently
- Normalizes text fields (removes extra whitespace, special characters)
- Converts prices to numeric format
- Extracts numeric ratings
- Calculates discount percentages
- Categorizes products by price range
- Adds metadata timestamps

### 3. Database Storage (loader.py)
- Creates SQLite database with proper schema
- Implements indexes for query optimization
- Handles duplicate entries
- Provides statistics and summary reports
- Maintains data integrity with UNIQUE constraints

### 4. Automation (Airflow DAG)
- Scheduled to run daily at 2:00 AM
- Four-stage pipeline:
  1. Scrape data from website
  2. Clean and preprocess data
  3. Load into database
  4. Generate summary report
- Implements retry logic (2 retries, 5-minute delay)
- Uses XCom for task communication
- Comprehensive logging at each stage

## Database Schema

### Table: products

| Column            | Type    | Description                          |
|-------------------|---------|--------------------------------------|
| id                | INTEGER | Primary key (auto-increment)         |
| product_id        | TEXT    | Product identifier from website      |
| product_name      | TEXT    | Product name (NOT NULL)              |
| price             | REAL    | Current price in KZT (NOT NULL)      |
| old_price         | REAL    | Original price (if discounted)       |
| discount_percent  | REAL    | Discount percentage                  |
| rating            | REAL    | Product rating (0-5)                 |
| availability      | TEXT    | Stock availability status            |
| product_url       | TEXT    | Link to product page                 |
| price_category    | TEXT    | Budget/Mid-range/Premium/Luxury      |
| scraped_at        | TEXT    | When data was scraped                |
| cleaned_at        | TEXT    | When data was cleaned                |
| loaded_at         | TEXT    | When data was loaded to DB           |

**Indexes:**
- idx_product_id (on product_id)
- idx_price (on price)
- idx_rating (on rating)
- idx_price_category (on price_category)

**Constraints:**
- UNIQUE(product_id, product_name) - prevents duplicates

## Installation & Setup

### Prerequisites
- Chrome browser (for Selenium)
- ChromeDriver (automatically managed by webdriver-manager)

### Step 1: Install Dependencies

```bash
cd dns_shop_pipeline
pip install -r requirements.txt
```

### Step 2: Initialize Database Schema

```bash
python create_schema.py
```

This will create the SQLite database with the proper schema and indexes.

### Step 3: Set Up Airflow

```bash
# Set Airflow home directory
export AIRFLOW_HOME=$(pwd)

# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin

# Copy DAG to Airflow dags folder
mkdir -p $AIRFLOW_HOME/dags
cp dags/dns_shop_dag.py $AIRFLOW_HOME/dags/
```

## Running the Pipeline

### Option 1: Run Individual Components

#### Run Scraper Only
```bash
python src/scraper.py
```
Output: `data/raw_products.json`

#### Run Cleaner Only
```bash
python src/cleaner.py
```
Output: `data/cleaned_products.csv`

#### Run Loader Only
```bash
python src/loader.py
```
Output: Updates `data/output.db`

### Option 2: Run Complete Pipeline Manually

```bash
# Run all steps in sequence
python src/scraper.py && python src/cleaner.py && python src/loader.py
```

### Option 3: Run with Airflow (Automated)

#### Start Airflow Services

Terminal 1 - Start Scheduler:
```bash
export AIRFLOW_HOME=$(pwd)
airflow scheduler
```

Terminal 2 - Start Web Server:
```bash
export AIRFLOW_HOME=$(pwd)
airflow webserver --port 8080
```

#### Access Airflow UI
1. Open browser: http://localhost:8080
2. Login: username=admin, password=admin
3. Find DAG: `dns_shop_pipeline`
4. Enable the DAG (toggle switch)
5. Trigger manually (play button) or wait for scheduled run

#### Monitor Execution
- View task logs in Airflow UI
- Check status of each task (scrape → clean → load → summary)
- Review XCom values for data counts

## Expected Output

### After Successful Run:

1. **Raw Data** (`data/raw_products.json`):
   - 100+ product records
   - JSON format with all scraped fields

2. **Cleaned Data** (`data/cleaned_products.csv`):
   - 100+ cleaned records
   - CSV format with normalized fields
   - Removed duplicates and invalid entries

3. **Database** (`data/output.db`):
   - SQLite database with products table
   - 100+ records with proper schema
   - Indexed for fast queries

4. **Logs**:
   - Detailed execution logs in Airflow UI
   - Timestamp for each operation
   - Record counts at each stage
   - Summary statistics

### Sample Statistics:
```
Total products: 120
Average price: 350,000 KZT
Price range: 150,000 - 800,000 KZT
Average rating: 4.3
Products with discount: 25
Price categories: Budget (30), Mid-range (50), Premium (30), Luxury (10)
```

## Querying the Database

### Connect to Database
```bash
sqlite3 data/output.db
```

### Sample Queries

```sql
-- View all products
SELECT * FROM products LIMIT 10;

-- Products by price category
SELECT price_category, COUNT(*) as count 
FROM products 
GROUP BY price_category;

-- Top rated products
SELECT product_name, price, rating 
FROM products 
WHERE rating > 4.5 
ORDER BY rating DESC 
LIMIT 10;

-- Products with discounts
SELECT product_name, price, old_price, discount_percent 
FROM products 
WHERE discount_percent > 0 
ORDER BY discount_percent DESC;

-- Average price by category
SELECT price_category, 
       ROUND(AVG(price), 2) as avg_price,
       COUNT(*) as product_count
FROM products 
GROUP BY price_category;
```

## Airflow DAG Details

**DAG ID:** `dns_shop_pipeline`

**Schedule:** Daily at 2:00 AM (`0 2 * * *`)

**Tasks:**
1. `scrape_data` - Scrapes DNS Shop website
2. `clean_data` - Cleans and preprocesses data
3. `load_data` - Loads into SQLite database
4. `pipeline_summary` - Generates execution summary

**Configuration:**
- Retries: 2
- Retry delay: 5 minutes
- Execution timeout: 30 minutes
- Catchup: False (only runs for current date)

## Troubleshooting

### Issue: Selenium can't find Chrome
**Solution:** Install Chrome and ChromeDriver
```bash
pip install webdriver-manager
```

### Issue: Airflow DAG not appearing
**Solution:** 
- Check DAG is in correct folder: `$AIRFLOW_HOME/dags/`
- Check for Python errors: `python dags/dns_shop_dag.py`
- Refresh Airflow UI

### Issue: Less than 100 records after cleaning
**Solution:** 
- Increase `max_products` in scraper (line 146)
- Increase `max_scrolls` in scraper (line 47)
- Check website availability

### Issue: Database locked error
**Solution:**
- Close any open database connections
- Delete `output.db` and recreate with `create_schema.py`

## Data Quality Checks

The pipeline includes several quality checks:
- Minimum 100 records after cleaning
- No duplicates (based on product_id + name)
- Essential fields (name, price) must not be null
- Prices converted to numeric format
- Ratings normalized to 0-5 scale
- Timestamps added at each stage

## Performance Metrics

- Scraping: ~2-3 minutes for 150 products
- Cleaning: ~5-10 seconds
- Loading: ~1-2 seconds
- Total pipeline: ~3-5 minutes

## Team Members

- **Daniil** - KBTU 
- **Bakytzhan** - KBTU 

