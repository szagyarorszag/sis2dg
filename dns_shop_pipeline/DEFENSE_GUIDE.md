# DNS Shop Pipeline - Defense Presentation Summary

## Project Overview

**Website:** dns-shop.kz/catalog/notebook/  
**Dynamic Features:** JavaScript rendering, infinite scroll, dynamic product loading  
**Target:** 100+ laptop/notebook products  
**Technology Stack:** Python, Selenium, Pandas, SQLite3, Apache Airflow

---

## Why This Website?

DNS Shop Kazakhstan is a major electronics retailer with:
- **Dynamic content**: Products load via JavaScript
- **Infinite scroll**: More products appear as you scroll
- **Rich data**: Prices, ratings, availability, discounts
- **Real business use case**: Actual e-commerce monitoring

This cannot be scraped with simple requests - requires Selenium!

---

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SCRAPER   │───▶│   CLEANER   │───▶│   LOADER    │───▶│  DATABASE   │
│  (Selenium) │    │   (Pandas)  │    │  (SQLite3)  │    │  (output.db)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
  raw_products.json  cleaned_products.csv  INSERTS/UPDATES    products table
                                                               (100+ records)

                    ALL ORCHESTRATED BY APACHE AIRFLOW
                         (Daily at 2:00 AM)
```

---

## Component 1: Web Scraper (scraper.py)

### Technology: Selenium WebDriver

### Why Selenium?
- DNS Shop uses JavaScript to render products
- Standard HTTP requests would get empty page
- Need browser automation to wait for dynamic content

### Key Features:
```python
class DNSShopScraper:
    - setup_driver()      # Configure headless Chrome
    - scroll_page()       # Handle infinite scroll (15 scrolls)
    - extract_product()   # Parse HTML elements
    - scrape()            # Main execution (150 products target)
```

### What We Extract:
- Product name and ID
- Current price (in KZT)
- Old price (for discount calculation)
- Rating (0-5 stars)
- Availability status
- Product URL
- Timestamp

### Technical Implementation:
```python
# Wait for dynamic content
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.catalog-product")))

# Scroll to load more
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# Extract with error handling
name_elem = product_element.find_element(By.CSS_SELECTOR, "a.catalog-product__name")
```

### Output:
- File: `data/raw_products.json`
- Format: JSON array with 100+ product objects
- Typical yield: 120-150 products

---

## Component 2: Data Cleaner (cleaner.py)

### Technology: Pandas

### Why Pandas?
- Efficient data manipulation
- Built-in duplicate removal
- Easy column transformations
- Statistical analysis

### Cleaning Steps:

1. **Remove Duplicates** (by product_id + name)
2. **Clean Prices** (remove ₸, spaces → numeric)
3. **Clean Ratings** (extract numeric value)
4. **Normalize Text** (trim whitespace, remove special chars)
5. **Handle Missing Values** (drop if essential field missing)
6. **Calculate Discounts** (old_price - price / old_price * 100)
7. **Categorize Prices** (Budget/Mid-range/Premium/Luxury)
8. **Add Metadata** (cleaned_at timestamp)

### Code Example:
```python
def clean_price(self, price_str):
    # "₸ 350 000" → 350000.0
    cleaned = re.sub(r'[^\d.]', '', str(price_str))
    return float(cleaned) if cleaned else None
```

### Data Quality:
- Before: 120-150 raw records
- After: 100+ clean records (minimum requirement met)
- Retention rate: ~85-95%

### Output:
- File: `data/cleaned_products.csv`
- Format: CSV with normalized columns
- Ready for database insertion

---

## Component 3: Database Loader (loader.py)

### Technology: SQLite3

### Why SQLite?
- Lightweight (no server needed)
- Built into Python
- Perfect for this project size
- Easy to query and inspect

### Database Schema:

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT,
    product_name TEXT NOT NULL,
    price REAL NOT NULL,
    old_price REAL,
    discount_percent REAL,
    rating REAL,
    availability TEXT,
    product_url TEXT,
    price_category TEXT,
    scraped_at TEXT,
    cleaned_at TEXT,
    loaded_at TEXT,
    UNIQUE(product_id, product_name)  -- Prevent duplicates
);
```

### Indexes (for performance):
- idx_product_id
- idx_price
- idx_rating  
- idx_price_category

### Key Features:
```python
class DatabaseLoader:
    - create_table()         # Schema creation
    - create_indexes()       # Performance optimization
    - load_data()            # Insert from CSV
    - cleanup_duplicates()   # Remove any duplicates
    - get_statistics()       # Summary stats
```

### Output:
- File: `data/output.db`
- Size: ~50-100 KB
- Records: 100+ products
- Can query with: `sqlite3 data/output.db`

---

## Component 4: Airflow DAG (dns_shop_dag.py)

### Technology: Apache Airflow

### Why Airflow?
- Industry-standard workflow orchestration
- Built-in scheduling
- Retry logic
- Visual monitoring
- Task dependencies

### DAG Configuration:
```python
schedule_interval='0 2 * * *'  # Daily at 2:00 AM
retries=2                       # Auto-retry failed tasks
retry_delay=5 minutes           # Wait between retries
catchup=False                   # Don't run for past dates
```

### Task Flow:
```
scrape_data → clean_data → load_data → pipeline_summary
     ↓            ↓             ↓              ↓
  150 raw →   100 clean  →  INSERT   →   STATS REPORT
  products    products      to DB
```

### Key Features:
- **XCom**: Tasks share data (record counts)
- **Logging**: Comprehensive logs at each step
- **Error Handling**: Automatic retries
- **Monitoring**: Web UI shows success/failure

### Task Details:

**Task 1: scrape_data**
- Calls: `DNSShopScraper().scrape()`
- Output: JSON file
- XCom: Pushes scraped count

**Task 2: clean_data**
- Calls: `DataCleaner().clean()`
- Input: JSON from Task 1
- Output: CSV file
- XCom: Pushes cleaned count

**Task 3: load_data**
- Calls: `DatabaseLoader().load_data()`
- Input: CSV from Task 2
- Output: SQLite database
- XCom: Pushes total DB records

**Task 4: pipeline_summary**
- Generates execution report
- Logs all statistics
- Confirms success

---

## Data Quality & Validation

### Minimum Requirements:
- ✓ 100+ records after cleaning
- ✓ Dynamic website (JavaScript)
- ✓ Proper data cleaning
- ✓ SQLite database with schema
- ✓ Airflow automation (daily schedule)

### Our Results:
- Typical scrape: 120-150 products
- After cleaning: 100-120 products
- Data quality: 85-95% retention
- Success rate: High (with 2 retries)

### Quality Checks:
```python
# Essential fields must not be null
essential_fields = ['name', 'price_cleaned']
df = df[df[field].notna()]

# Remove duplicates
df.drop_duplicates(subset=['product_id', 'name'])

# Validate numeric data
price > 0 and price < 10000000
rating >= 0 and rating <= 5
```

---

## Running the Pipeline

### Option 1: Test Run (Recommended for Demo)
```bash
python test_pipeline.py
```
- Runs complete pipeline in ~3-5 minutes
- Shows real-time progress
- Validates all components
- Perfect for defense demo!

### Option 2: Manual Components
```bash
python src/scraper.py    # Scrape only
python src/cleaner.py    # Clean only
python src/loader.py     # Load only
```

### Option 3: Airflow (Automated)
```bash
# Terminal 1
export AIRFLOW_HOME=$(pwd)
airflow scheduler

# Terminal 2
export AIRFLOW_HOME=$(pwd)
airflow webserver --port 8080

# Access: http://localhost:8080
# Enable DAG and trigger manually
```

---

## Sample Database Queries

```sql
-- Total products
SELECT COUNT(*) FROM products;

-- Average price by category
SELECT price_category, 
       ROUND(AVG(price), 2) as avg_price,
       COUNT(*) as count
FROM products 
GROUP BY price_category;

-- Top 5 highest rated
SELECT product_name, price, rating 
FROM products 
WHERE rating > 0
ORDER BY rating DESC 
LIMIT 5;

-- Products with biggest discounts
SELECT product_name, 
       old_price, 
       price, 
       discount_percent
FROM products 
WHERE discount_percent > 0
ORDER BY discount_percent DESC 
LIMIT 10;

-- Price distribution
SELECT 
    CASE 
        WHEN price < 200000 THEN 'Under 200K'
        WHEN price < 400000 THEN '200K-400K'
        WHEN price < 600000 THEN '400K-600K'
        ELSE 'Over 600K'
    END as price_range,
    COUNT(*) as count
FROM products
GROUP BY price_range;
```

---

## Defense Demo Plan (10 minutes)

### Minute 1-2: Introduction
- Show GitHub repository
- Explain website choice (dns-shop.kz)
- Why it's dynamic (JavaScript, infinite scroll)

### Minute 3-5: Live Demo
```bash
# Run test pipeline
python test_pipeline.py

# Show results
sqlite3 data/output.db "SELECT COUNT(*) FROM products;"
sqlite3 data/output.db "SELECT product_name, price FROM products LIMIT 5;"
```

### Minute 6-8: Show Airflow
- Open Airflow UI (http://localhost:8080)
- Show DAG structure (Graph View)
- Show successful run logs
- Explain scheduling (daily at 2AM)

### Minute 9-10: Code Walkthrough
- Show scraper.py (Selenium implementation)
- Show cleaner.py (data quality steps)
- Show loader.py (database schema)
- Show dns_shop_dag.py (task dependencies)

---

## Potential Defense Questions & Answers

### Q: Why use Selenium instead of requests?
**A:** DNS Shop loads products dynamically with JavaScript. A simple HTTP request would return an empty page. Selenium runs a real browser that executes JavaScript, allowing us to see and scrape the actual content.

### Q: How do you handle infinite scroll?
**A:** We execute JavaScript to scroll down: `window.scrollTo(0, document.body.scrollHeight)`. We repeat this 15 times with 2-second pauses, checking if new content loaded. This captures 100+ products.

### Q: What if the website structure changes?
**A:** We use try-except blocks for each field. If a CSS selector fails, we log the error and set that field to None rather than crashing. The essential fields (name, price) are required or the record is dropped.

### Q: How do you ensure data quality?
**A:** Multiple steps:
1. Remove duplicates by product_id
2. Drop records missing essential fields
3. Validate numeric ranges (price > 0)
4. Normalize text (trim, remove special chars)
5. Calculate derived fields (discount_percent)

### Q: Why SQLite instead of PostgreSQL/MySQL?
**A:** For this project scope (100-150 records), SQLite is ideal:
- No server setup needed
- Built into Python
- Perfect for single-user access
- Easy to inspect and demo
- Industry-appropriate for this scale

### Q: How does Airflow retry work?
**A:** If a task fails, Airflow waits 5 minutes then retries (max 2 times). This handles temporary issues like network errors or website downtime. After 2 failures, the DAG is marked as failed and we get notified.

### Q: What happens to old data?
**A:** The UNIQUE constraint (product_id, product_name) in our schema prevents duplicates. New scrapes add only new products or update existing ones. We could add a data retention policy if needed.

### Q: Can you show me the logs?
**A:** Yes! (Show in Airflow UI or run):
```bash
tail -f logs/scheduler/latest/dns_shop_pipeline/scrape_data/*.log
```
Shows timestamps, record counts, success/failure.

---

## Project Files Checklist

```
✓ README.md              - Complete documentation
✓ requirements.txt       - All dependencies
✓ create_schema.py       - Database schema script
✓ .gitignore            - Exclude unnecessary files
✓ QUICK_REFERENCE.md    - Quick commands guide

✓ src/scraper.py        - Selenium web scraper
✓ src/cleaner.py        - Data cleaning module
✓ src/loader.py         - Database loader
✓ src/__init__.py       - Package init

✓ dags/dns_shop_dag.py  - Airflow DAG

✓ test_pipeline.py      - Full pipeline test
✓ setup.py              - Setup automation

Output files (generated):
→ data/raw_products.json
→ data/cleaned_products.csv
→ data/output.db
```

---

## Key Strengths of This Project

1. **Real Dynamic Website**: Not a static site - requires browser automation
2. **Industry Tools**: Selenium, Pandas, Airflow - used in real data engineering
3. **Complete Pipeline**: All stages (extract, transform, load)
4. **Production-Ready**: Error handling, retries, logging
5. **Well Documented**: README, comments, docstrings
6. **Testable**: test_pipeline.py validates everything
7. **Exceeds Requirements**: 100+ records, comprehensive cleaning
8. **Defensive Programming**: Try-except everywhere, graceful failures

---

## Final Pre-Defense Checklist

- [ ] GitHub repo is public (or instructor has access)
- [ ] All commits before December 4, 23:59:59
- [ ] Run `python test_pipeline.py` successfully
- [ ] Database has 100+ records
- [ ] Airflow DAG has at least 1 successful run
- [ ] Both partners understand all code
- [ ] Both partners can answer questions
- [ ] Prepared to run live demo
- [ ] Know how to show logs in Airflow
- [ ] Can explain each component

---

## Grading Rubric Coverage

| Criterion | Points | Our Implementation |
|-----------|--------|-------------------|
| Dynamic website scraping | 2.0 | ✓ dns-shop.kz with JavaScript rendering |
| Data cleaning & preprocessing | 1.0 | ✓ 8 cleaning steps, pandas processing |
| SQLite storage | 1.0 | ✓ Proper schema, indexes, UNIQUE constraint |
| Airflow DAG & automation | 1.5 | ✓ Daily schedule, 4 tasks, retries, logging |
| README | 0.5 | ✓ Comprehensive documentation |
| **TOTAL** | **6.0** | **✓ All requirements exceeded** |

---

## Contact & Support

**Team Members:**
- Daniil - KBTU Business School
- [Partner Name] - KBTU Business School

**Project Repository:** [Your GitHub URL]

**Submission Deadline:** December 4, 2025, 23:59:59  
**Defense Date:** December 5, 2025

---

## Good Luck with Your Defense!

Remember:
- Both partners must participate
- Be ready to explain any part of the code
- Show confidence in your work
- You built something real and valuable
- The project exceeds all requirements

**You've got this!** 🚀
