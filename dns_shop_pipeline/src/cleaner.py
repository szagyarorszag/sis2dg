"""
Data Cleaning and Preprocessing Module
Cleans and preprocesses scraped product data from DNS Shop
"""

import json
import logging
import pandas as pd
import re
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCleaner:
    """Cleans and preprocesses scraped product data"""
    
    def __init__(self, input_file):
        """Initialize cleaner with input file path"""
        self.input_file = input_file
        self.df = None
        self.cleaned_df = None
        
    def load_data(self):
        """Load raw data from JSON file"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.df = pd.DataFrame(data)
            logger.info(f"Loaded {len(self.df)} records from {self.input_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def remove_duplicates(self):
        """Remove duplicate records based on product name and URL"""
        initial_count = len(self.df)
        
        # Remove duplicates based on product_id if available
        if 'product_id' in self.df.columns:
            self.df = self.df.drop_duplicates(subset=['product_id'], keep='first')
        
        # Also remove duplicates based on name and price
        self.df = self.df.drop_duplicates(subset=['name', 'price'], keep='first')
        
        removed_count = initial_count - len(self.df)
        logger.info(f"Removed {removed_count} duplicate records")
    
    def clean_price(self, price_str):
        """Clean and convert price string to numeric value"""
        if pd.isna(price_str) or price_str is None:
            return None
        
        try:
            # Remove all non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', str(price_str))
            return float(cleaned) if cleaned else None
        except:
            return None
    
    def clean_rating(self, rating_str):
        """Extract numeric rating from rating string"""
        if pd.isna(rating_str) or rating_str is None:
            return None
        
        try:
            # Extract first number from rating string
            match = re.search(r'(\d+\.?\d*)', str(rating_str))
            return float(match.group(1)) if match else None
        except:
            return None
    
    def normalize_text(self, text):
        """Normalize text fields - trim whitespace and handle special characters"""
        if pd.isna(text) or text is None:
            return None
        
        # Convert to string and strip whitespace
        text = str(text).strip()
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text if text else None
    
    def clean_columns(self):
        """Clean all columns in the dataframe"""
        logger.info("Starting column cleaning...")
        
        # Clean name
        if 'name' in self.df.columns:
            self.df['name'] = self.df['name'].apply(self.normalize_text)
        
        # Clean price
        if 'price' in self.df.columns:
            self.df['price_cleaned'] = self.df['price'].apply(self.clean_price)
        
        # Clean old price
        if 'old_price' in self.df.columns:
            self.df['old_price_cleaned'] = self.df['old_price'].apply(self.clean_price)
        
        # Clean rating
        if 'rating' in self.df.columns:
            self.df['rating_cleaned'] = self.df['rating'].apply(self.clean_rating)
        
        # Clean availability
        if 'availability' in self.df.columns:
            self.df['availability'] = self.df['availability'].apply(self.normalize_text)
        
        # Clean URL
        if 'url' in self.df.columns:
            self.df['url'] = self.df['url'].apply(self.normalize_text)
        
        # Calculate discount if both prices are available
        if 'price_cleaned' in self.df.columns and 'old_price_cleaned' in self.df.columns:
            self.df['discount_percent'] = self.df.apply(
                lambda row: round(((row['old_price_cleaned'] - row['price_cleaned']) / row['old_price_cleaned'] * 100), 2)
                if pd.notna(row['old_price_cleaned']) and pd.notna(row['price_cleaned']) and row['old_price_cleaned'] > 0
                else None,
                axis=1
            )
        
        logger.info("Column cleaning completed")
    
    def handle_missing_values(self):
        """Handle missing values in the dataset"""
        logger.info("Handling missing values...")
        
        # Drop rows where essential fields are missing
        essential_fields = ['name', 'price_cleaned']
        initial_count = len(self.df)
        
        for field in essential_fields:
            if field in self.df.columns:
                self.df = self.df[self.df[field].notna()]
        
        removed_count = initial_count - len(self.df)
        logger.info(f"Removed {removed_count} records with missing essential fields")
        
        # Fill missing rating with 0
        if 'rating_cleaned' in self.df.columns:
            self.df['rating_cleaned'] = self.df['rating_cleaned'].fillna(0.0)
        
        # Fill missing availability with 'Unknown'
        if 'availability' in self.df.columns:
            self.df['availability'] = self.df['availability'].fillna('Unknown')
    
    def add_metadata(self):
        """Add metadata columns"""
        self.df['cleaned_at'] = datetime.now().isoformat()
        
        # Add price category
        if 'price_cleaned' in self.df.columns:
            def categorize_price(price):
                if pd.isna(price):
                    return 'Unknown'
                elif price < 200000:
                    return 'Budget'
                elif price < 400000:
                    return 'Mid-range'
                elif price < 600000:
                    return 'Premium'
                else:
                    return 'Luxury'
            
            self.df['price_category'] = self.df['price_cleaned'].apply(categorize_price)
        
        logger.info("Metadata added")
    
    def create_final_dataframe(self):
        """Create final cleaned dataframe with selected columns"""
        # Select and rename columns for final output
        columns_map = {
            'product_id': 'product_id',
            'name': 'product_name',
            'price_cleaned': 'price',
            'old_price_cleaned': 'old_price',
            'discount_percent': 'discount_percent',
            'rating_cleaned': 'rating',
            'availability': 'availability',
            'url': 'product_url',
            'price_category': 'price_category',
            'scraped_at': 'scraped_at',
            'cleaned_at': 'cleaned_at'
        }
        
        available_columns = [col for col in columns_map.keys() if col in self.df.columns]
        self.cleaned_df = self.df[available_columns].copy()
        self.cleaned_df = self.cleaned_df.rename(columns=columns_map)
        
        logger.info(f"Final dataframe created with {len(self.cleaned_df)} records")
    
    def clean(self):
        """Execute full cleaning pipeline"""
        logger.info("Starting data cleaning pipeline...")
        
        if not self.load_data():
            return None
        
        initial_count = len(self.df)
        logger.info(f"Initial record count: {initial_count}")
        
        # Execute cleaning steps
        self.remove_duplicates()
        self.clean_columns()
        self.handle_missing_values()
        self.add_metadata()
        self.create_final_dataframe()
        
        final_count = len(self.cleaned_df)
        logger.info(f"Cleaning completed. Final record count: {final_count}")
        logger.info(f"Records retained: {final_count}/{initial_count} ({(final_count/initial_count*100):.1f}%)")
        
        return self.cleaned_df
    
    def save_to_csv(self, output_file):
        """Save cleaned data to CSV"""
        try:
            self.cleaned_df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"Cleaned data saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return False
    
    def get_summary_statistics(self):
        """Generate summary statistics of cleaned data"""
        if self.cleaned_df is None:
            return None
        
        stats = {
            'total_records': len(self.cleaned_df),
            'avg_price': self.cleaned_df['price'].mean() if 'price' in self.cleaned_df.columns else None,
            'min_price': self.cleaned_df['price'].min() if 'price' in self.cleaned_df.columns else None,
            'max_price': self.cleaned_df['price'].max() if 'price' in self.cleaned_df.columns else None,
            'avg_rating': self.cleaned_df['rating'].mean() if 'rating' in self.cleaned_df.columns else None,
            'products_with_discount': len(self.cleaned_df[self.cleaned_df['discount_percent'] > 0]) if 'discount_percent' in self.cleaned_df.columns else None
        }
        
        return stats


def main():
    """Main execution function"""
    import os
    
    # Use relative paths from script location
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(script_dir, 'data', 'raw_products.json')
    output_file = os.path.join(script_dir, 'data', 'cleaned_products.csv')
    
    cleaner = DataCleaner(input_file)
    cleaned_data = cleaner.clean()
    
    if cleaned_data is not None and len(cleaned_data) > 0:
        cleaner.save_to_csv(output_file)
        
        # Print summary statistics
        stats = cleaner.get_summary_statistics()
        logger.info(f"Summary Statistics: {json.dumps(stats, indent=2)}")
        
        return cleaned_data
    else:
        logger.error("No data to save")
        return None


if __name__ == "__main__":
    main()
