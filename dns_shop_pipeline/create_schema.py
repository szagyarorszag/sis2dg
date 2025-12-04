import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'data', 'output.db')

def create_database_schema():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    if os.path.exists(DB_PATH):
        print(f"Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Creating database: {DB_PATH}")
    
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
    
    indexes = [
        ("idx_product_id", "CREATE INDEX IF NOT EXISTS idx_product_id ON products(product_id);"),
        ("idx_price", "CREATE INDEX IF NOT EXISTS idx_price ON products(price);"),
        ("idx_rating", "CREATE INDEX IF NOT EXISTS idx_rating ON products(rating);"),
        ("idx_price_category", "CREATE INDEX IF NOT EXISTS idx_price_category ON products(price_category);"),
    ]
    
    for index_name, index_sql in indexes:
        cursor.execute(index_sql)
        print(f"created index '{index_name}'")
    
    conn.commit()

    
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    
    print("\nTable: products")
    print(f"{'Column':<20} {'Type':<15} {'NotNull':<10} {'PK':<5}")
    
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        print(f"{name:<20} {col_type:<15} {'Yes' if not_null else 'No':<10} {'Yes' if pk else 'No':<5}")
    
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='products'")
    indexes = cursor.fetchall()
    
    for idx_name, idx_sql in indexes:
        if idx_sql:
            print(f"\n{idx_name}:")
            print(f"  {idx_sql}")
    
    print("schema created")
    
    conn.close()


if __name__ == "__main__":
    create_database_schema()