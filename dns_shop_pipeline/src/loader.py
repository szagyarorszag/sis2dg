"""
Database Loader Module
Loads cleaned data into SQLite database
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Loads cleaned data into SQLite database"""
    
    def __init__(self, db_path):
        """Initialize loader with database path"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    
    def create_table(self):
        """Create products table with proper schema"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS products (
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
            UNIQUE(product_id, product_name)
        );
        """
        
        try:
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            logger.info("Products table created/verified successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating table: {e}")
            return False
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_product_id ON products(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_price ON products(price);",
            "CREATE INDEX IF NOT EXISTS idx_rating ON products(rating);",
            "CREATE INDEX IF NOT EXISTS idx_price_category ON products(price_category);"
        ]
        
        try:
            for index_sql in indexes:
                self.cursor.execute(index_sql)
            self.conn.commit()
            logger.info("Indexes created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return False
    
    def load_data(self, csv_file):
        """Load data from CSV file into database"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded {len(df)} records from {csv_file}")
            
            # Add loaded_at timestamp
            df['loaded_at'] = datetime.now().isoformat()
            
            # Insert data using pandas to_sql with replace mode
            # This will replace existing records with same product_id
            records_before = self.get_record_count()
            
            # Use append mode to add new records
            df.to_sql('products', self.conn, if_exists='append', index=False)
            
            records_after = self.get_record_count()
            new_records = records_after - records_before
            
            logger.info(f"Successfully loaded {new_records} new records into database")
            logger.info(f"Total records in database: {records_after}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def get_record_count(self):
        """Get total number of records in products table"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM products")
            count = self.cursor.fetchone()[0]
            return count
        except:
            return 0
    
    def get_latest_records(self, limit=10):
        """Retrieve latest records from database"""
        try:
            query = """
            SELECT product_name, price, rating, availability, price_category, loaded_at
            FROM products
            ORDER BY loaded_at DESC
            LIMIT ?
            """
            self.cursor.execute(query, (limit,))
            records = self.cursor.fetchall()
            return records
        except Exception as e:
            logger.error(f"Error retrieving records: {e}")
            return []
    
    def get_statistics(self):
        """Get database statistics"""
        try:
            stats = {}
            
            # Total products
            self.cursor.execute("SELECT COUNT(*) FROM products")
            stats['total_products'] = self.cursor.fetchone()[0]
            
            # Average price
            self.cursor.execute("SELECT AVG(price) FROM products")
            stats['avg_price'] = round(self.cursor.fetchone()[0], 2) if stats['total_products'] > 0 else 0
            
            # Price range
            self.cursor.execute("SELECT MIN(price), MAX(price) FROM products")
            min_price, max_price = self.cursor.fetchone()
            stats['min_price'] = min_price
            stats['max_price'] = max_price
            
            # Products by category
            self.cursor.execute("""
                SELECT price_category, COUNT(*) 
                FROM products 
                GROUP BY price_category
            """)
            stats['by_category'] = dict(self.cursor.fetchall())
            
            # Average rating
            self.cursor.execute("SELECT AVG(rating) FROM products WHERE rating > 0")
            avg_rating = self.cursor.fetchone()[0]
            stats['avg_rating'] = round(avg_rating, 2) if avg_rating else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def cleanup_duplicates(self):
        """Remove duplicate entries keeping the most recent one"""
        try:
            cleanup_sql = """
            DELETE FROM products
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM products
                GROUP BY product_id, product_name
            )
            """
            self.cursor.execute(cleanup_sql)
            deleted_count = self.cursor.rowcount
            self.conn.commit()
            logger.info(f"Cleaned up {deleted_count} duplicate records")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up duplicates: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def main():
    """Main execution function"""
    import os
    
    # Use relative paths from script location
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(script_dir, 'data', 'output.db')
    csv_file = os.path.join(script_dir, 'data', 'cleaned_products.csv')
    
    loader = DatabaseLoader(db_path)
    
    if loader.connect():
        # Create table and indexes
        loader.create_table()
        loader.create_indexes()
        
        # Load data
        if loader.load_data(csv_file):
            # Cleanup duplicates
            loader.cleanup_duplicates()
            
            # Get and display statistics
            stats = loader.get_statistics()
            logger.info(f"Database Statistics:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
            
            # Display latest records
            latest = loader.get_latest_records(5)
            logger.info(f"\nLatest 5 records:")
            for record in latest:
                logger.info(f"  {record}")
        
        loader.close()


if __name__ == "__main__":
    main()
