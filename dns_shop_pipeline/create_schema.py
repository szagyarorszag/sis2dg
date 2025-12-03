"""
Database Schema Creation Script
Creates the SQLite database schema for DNS Shop products
"""

import sqlite3
import os

# Use relative path from script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'data', 'output.db')

def create_database_schema():
    """Create database schema with proper table structure"""
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Remove existing database if it exists (for fresh start)
    if os.path.exists(DB_PATH):
        print(f"Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)
    
    # Connect to database (creates new file)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Creating database: {DB_PATH}")
    
    # Create products table
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
    
    cursor.execute(create_table_sql)
    print("✓ Created 'products' table")
    
    # Create indexes for better query performance
    indexes = [
        ("idx_product_id", "CREATE INDEX IF NOT EXISTS idx_product_id ON products(product_id);"),
        ("idx_price", "CREATE INDEX IF NOT EXISTS idx_price ON products(price);"),
        ("idx_rating", "CREATE INDEX IF NOT EXISTS idx_rating ON products(rating);"),
        ("idx_price_category", "CREATE INDEX IF NOT EXISTS idx_price_category ON products(price_category);"),
    ]
    
    for index_name, index_sql in indexes:
        cursor.execute(index_sql)
        print(f"✓ Created index '{index_name}'")
    
    conn.commit()
    
    # Display schema
    print("\n" + "="*60)
    print("DATABASE SCHEMA")
    print("="*60)
    
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    
    print("\nTable: products")
    print("-" * 60)
    print(f"{'Column':<20} {'Type':<15} {'NotNull':<10} {'PK':<5}")
    print("-" * 60)
    
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        print(f"{name:<20} {col_type:<15} {'Yes' if not_null else 'No':<10} {'Yes' if pk else 'No':<5}")
    
    print("\n" + "="*60)
    print("INDEXES")
    print("="*60)
    
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='products'")
    indexes = cursor.fetchall()
    
    for idx_name, idx_sql in indexes:
        if idx_sql:  # Skip auto-created indexes
            print(f"\n{idx_name}:")
            print(f"  {idx_sql}")
    
    print("\n" + "="*60)
    print("Schema created successfully!")
    print("="*60)
    
    conn.close()


if __name__ == "__main__":
    create_database_schema()
