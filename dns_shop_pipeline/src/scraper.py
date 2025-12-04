import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DNSShopScraper:
    
    def __init__(self, headless=True):
        self.url = "https://dns-shop.kz/"
        self.products = []
        self.headless = headless
        
    def setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    
    def scroll_page(self, driver, scroll_pause_time=2, max_scrolls=10):
        logger.info("Starting page scroll to load dynamic content...")
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        
        while scrolls < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                logger.info(f"Reached end of page after {scrolls} scrolls")
                break
                
            last_height = new_height
            scrolls += 1
            logger.info(f"Scroll {scrolls}/{max_scrolls} completed")
        
        return scrolls
    
    def handle_city_modal(self, driver):
        try:
            wait = WebDriverWait(driver, 10)
            confirm_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Все верно')]"))
            )
            confirm_button.click()
            logger.info("Clicked city confirmation button")
            time.sleep(2)
            return True
        except TimeoutException:
            logger.warning("City modal not found or already dismissed")
            return False
        except Exception as e:
            logger.error(f"Error handling city modal: {e}")
            return False
    
    def navigate_to_tvs(self, driver):
        try:
            wait = WebDriverWait(driver, 15)
            tv_link = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Телевизоры"))
            )
            tv_link.click()
            logger.info("Navigated to TV category")
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"Error navigating to TV category: {e}")
            try:
                logger.info("Attempting direct URL navigation to TV category")
                driver.get("https://dns-shop.kz/catalog/17a8dc5916404e77/")
                time.sleep(3)
                return True
            except Exception as e2:
                logger.error(f"Direct navigation also failed: {e2}")
                return False
    
    def extract_product_data(self, product_element):
        try:
            product_data = {}
            
            try:
                name_elem = product_element.find_element(By.CSS_SELECTOR, "a.catalog-product__name")
                product_data['name'] = name_elem.text.strip()
                product_data['url'] = name_elem.get_attribute('href')
            except NoSuchElementException:
                product_data['name'] = None
                product_data['url'] = None
    
            try:
                price_elem = product_element.find_element(By.CSS_SELECTOR, "div.product-buy__price")
                price_text = price_elem.text.strip().replace('₸', '').replace(' ', '').replace('\xa0', '')
                product_data['price'] = price_text
            except NoSuchElementException:
                product_data['price'] = None
            
            try:
                old_price_elem = product_element.find_element(By.CSS_SELECTOR, "div.product-buy__price_old")
                old_price_text = old_price_elem.text.strip().replace('₸', '').replace(' ', '').replace('\xa0', '')
                product_data['old_price'] = old_price_text
            except NoSuchElementException:
                product_data['old_price'] = None
            
            try:
                rating_elem = product_element.find_element(By.CSS_SELECTOR, "div.catalog-product__rating")
                rating_text = rating_elem.text.strip()
                product_data['rating'] = rating_text
            except NoSuchElementException:
                product_data['rating'] = None
            
            try:
                availability_elem = product_element.find_element(By.CSS_SELECTOR, "div.catalog-product__availability")
                product_data['availability'] = availability_elem.text.strip()
            except NoSuchElementException:
                product_data['availability'] = None
            
            try:
                product_data['product_id'] = product_element.get_attribute('data-id')
            except:
                if product_data['url']:
                    url_parts = product_data['url'].split('/')
                    product_data['product_id'] = url_parts[-2] if len(url_parts) > 1 else None
                else:
                    product_data['product_id'] = None
            
            product_data['scraped_at'] = datetime.now().isoformat()
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None
    
    def scrape(self, max_products=150):
        logger.info(f"Starting scraper for {self.url}")
        driver = None
        
        try:
            driver = self.setup_driver()
            logger.info("WebDriver initialized successfully")
            
            driver.get(self.url)
            logger.info(f"Loaded homepage: {self.url}")
            time.sleep(2)
            
            self.handle_city_modal(driver)
            
            if not self.navigate_to_tvs(driver):
                logger.error("Failed to navigate to TV category")
                return []
            
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.catalog-product")))
            logger.info("Products container loaded")
            
            current_page = 1
            max_pages = 10 
            
            while len(self.products) < max_products and current_page <= max_pages:
                logger.info(f"Scraping page {current_page}...")
                
                time.sleep(2)
                
                product_elements = driver.find_elements(By.CSS_SELECTOR, "div.catalog-product")
                logger.info(f"Found {len(product_elements)} product elements on page {current_page}")
                
                products_on_page = 0
                for product_elem in product_elements:
                    if len(self.products) >= max_products:
                        break
                        
                    product_data = self.extract_product_data(product_elem)
                    
                    if product_data and product_data.get('name'):
                        self.products.append(product_data)
                        products_on_page += 1
                        logger.info(f"Extracted product {len(self.products)}: {product_data['name'][:50]}...")
                
                logger.info(f"Scraped {products_on_page} products from page {current_page}. Total: {len(self.products)}")
                
                if len(self.products) >= max_products:
                    logger.info(f"Reached target of {max_products} products")
                    break
                
                current_page += 1
                next_page_number = current_page
                
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    
                    next_page_link = wait.until(
                        EC.element_to_be_clickable((
                            By.XPATH, 
                            f"//a[@class='pagination-widget__page-link' and contains(text(), '{next_page_number}')]"
                        ))
                    )
                    
                    logger.info(f"Clicking page {next_page_number}...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_page_link)
                    time.sleep(0.5)
                    next_page_link.click()
                    
                    time.sleep(3)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.catalog-product")))
                    
                except TimeoutException:
                    logger.info(f"No more pages available after page {current_page - 1}")
                    break
                except Exception as e:
                    logger.warning(f"Could not navigate to page {next_page_number}: {e}")
                    break
            
            logger.info(f"Successfully scraped {len(self.products)} products across {current_page} pages")
            
        except TimeoutException:
            logger.error("Timeout waiting for page elements")
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            if driver:
                driver.quit()
                logger.info("WebDriver closed")
        
        return self.products
    
    def save_to_json(self, filepath):
        """Save scraped data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)
            logger.info(f"Data saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return False


def main():
    import os
    
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(script_dir, 'data', 'raw_products.json')
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    scraper = DNSShopScraper(headless=True)
    products = scraper.scrape(max_products=150)
    
    if products:
        scraper.save_to_json(output_file)
        logger.info(f"Scraping completed. Total products: {len(products)}")
    else:
        logger.warning("No products were scraped")
    
    return products


if __name__ == "__main__":
    main()