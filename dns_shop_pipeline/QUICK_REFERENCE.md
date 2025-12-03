# DNS Shop Pipeline - Quick Reference Guide

## Quick Start (5 Minutes)

```bash
# 1. Setup
python setup.py

# 2. Test pipeline
python test_pipeline.py

# 3. Create Airflow user
airflow users create --username admin --password admin \
  --firstname Admin --lastname User --role Admin \
  --email admin@example.com

# 4. Start Airflow (2 terminals)
# Terminal 1:
export AIRFLOW_HOME=$(pwd) && airflow scheduler

# Terminal 2:
export AIRFLOW_HOME=$(pwd) && airflow webserver --port 8080

# 5. Access UI: http://localhost:8080
```

## Common Commands

### Run Individual Components

```bash
# Scrape only
python src/scraper.py

# Clean only
python src/cleaner.py

# Load only
python src/loader.py

# Full pipeline
python test_pipeline.py
```

### Database Operations

```bash
# View database
sqlite3 data/output.db

# Quick queries
sqlite3 data/output.db "SELECT COUNT(*) FROM products;"
sqlite3 data/output.db "SELECT product_name, price FROM products LIMIT 5;"
sqlite3 data/output.db "SELECT price_category, COUNT(*) FROM products GROUP BY price_category;"
```

### Airflow Operations

```bash
# List DAGs
airflow dags list

# Test DAG
airflow dags test dns_shop_pipeline 2024-12-04

# Trigger DAG
airflow dags trigger dns_shop_pipeline

# View task logs
airflow tasks logs dns_shop_pipeline scrape_data 2024-12-04

# Pause/Unpause DAG
airflow dags pause dns_shop_pipeline
airflow dags unpause dns_shop_pipeline
```

### Debugging

```bash
# Check Airflow config
airflow config list

# Test Python imports
python -c "from src.scraper import DNSShopScraper; print('OK')"

# Check Chrome
which chromium || which google-chrome

# View logs
tail -f logs/scheduler/latest/dns_shop_pipeline/*.log
```

## File Locations

```
Raw data:     data/raw_products.json
Cleaned data: data/cleaned_products.csv
Database:     data/output.db
DAG file:     dags/dns_shop_dag.py
Logs:         logs/
```

## Troubleshooting

### Issue: No products scraped
```bash
# Run scraper with debug
python src/scraper.py

# Check if website is accessible
curl -I https://dns-shop.kz
```

### Issue: Airflow DAG not showing
```bash
# Check DAG syntax
python dags/dns_shop_dag.py

# Check AIRFLOW_HOME
echo $AIRFLOW_HOME

# Refresh DAGs
airflow dags list-import-errors
```

### Issue: Database locked
```bash
# Kill processes using database
lsof data/output.db

# Recreate database
python create_schema.py
```

## Defense Preparation

### What to Show:
1. GitHub repository (show commits before deadline)
2. Run `python test_pipeline.py` - show successful execution
3. Open database: `sqlite3 data/output.db` and run queries
4. Airflow UI - show DAG structure and successful run logs
5. Explain each component (scraper, cleaner, loader)

### Sample Questions to Prepare:
- How does Selenium handle dynamic content?
- What cleaning steps did you implement?
- Why SQLite instead of other databases?
- How does Airflow scheduling work?
- How do you handle duplicates?
- What happens if scraping fails?

### Key Points to Mention:
- Website uses JavaScript rendering (dynamic)
- Implemented page scrolling for infinite scroll
- 100+ records requirement met
- Proper error handling and retries
- Comprehensive logging
- Database indexes for performance

## Project Statistics

Target: 100+ records
Expected output: 120-150 products
Execution time: ~3-5 minutes
Schedule: Daily at 2:00 AM
Success rate: High (with retries)

## For Oral Defense

### Demo Flow (10 minutes):
1. Show GitHub repo (1 min)
2. Run test_pipeline.py (2 min)
3. Show database queries (2 min)
4. Show Airflow UI and logs (3 min)
5. Explain architecture (2 min)

### Both Partners Should Know:
- How scraping works
- What each cleaning step does
- Database schema
- DAG task flow
- How to run everything

## Submission Checklist

- [ ] All code committed to GitHub
- [ ] Commits before December 4, 23:59:59
- [ ] README.md complete
- [ ] requirements.txt included
- [ ] create_schema.py included
- [ ] At least one successful Airflow run
- [ ] Database has 100+ records
- [ ] Repository is public or instructor has access
- [ ] Both partners can explain the code
- [ ] Tested on clean environment

## Support

For issues during setup or execution:
1. Check logs in logs/ directory
2. Review README.md troubleshooting section
3. Test individual components
4. Verify all dependencies installed

Good luck with your defense!
