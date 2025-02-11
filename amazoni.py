import time
import csv
import json
import random
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================== Helper Functions ==================

def init_driver():
    """Initialize Safari WebDriver with proper configuration"""
    driver = webdriver.Safari()
    driver.maximize_window()  # FIXED: Added window maximization
    return driver

def scrape_product_page(driver):
    """Scrapes product page details with improved error handling"""
    data = {}
    
    # FIXED: Updated title selector and added tab handling
    
    try:
        # Handle potential new tab
        WebDriverWait(driver, 15).until(EC.number_of_windows_to_be(2))
        driver.switch_to.window(driver.window_handles[1])
        
        title_elem = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.module_title .product-title-container h1"))  # FIXED selector
        )
        data["Product Title"] = title_elem.text.strip()
        
    except Exception as e:
        title_elem = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.module_title .product-title-container h1"))  # FIXED selector
        )
        print(">>>>>>>>> title", title_elem)
        print("Could not extract product title:", e)
        data["Product Title"] = "N/A"
    finally:
        # Always save URL even if title fails
        data["Product URL"] = driver.current_url
    
    # FIXED: Attribute extraction with table existence check
    key_attributes = {}
    try:
        attribute_module = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-module-name='module_attribute']"))
        )
        
        attribute_items = attribute_module.find_elements(By.CSS_SELECTOR, ".attribute-item")
        for item in attribute_items:
            try:
                # Extract the key and value from each attribute item
                key = item.find_element(By.CSS_SELECTOR, ".left").text.strip()
                value = item.find_element(By.CSS_SELECTOR, ".right span").text.strip()
                key_attributes[key] = value
            except Exception as e:
                print(f"Error processing attribute item: {e}")

    except Exception as e:
     print("No attribute module found:", e)
    
    data["Key Attributes"] = key_attributes
    data["Date Scraped"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # FIXED: Consistent format
    return data

def save_to_csv(data_list, filename):
    """Save data to CSV with corrected key handling"""
    if not data_list:
        print("No data to save.")
        return

    # FIXED: Use correct "Key Attributes" field
    all_attr_keys = set()
    for item in data_list:
        attributes = item.get("Key Attributes", {})
        all_attr_keys.update(attributes.keys())

    fieldnames = ["Product Title", "Product URL", "Date Scraped"] + list(all_attr_keys)
    
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in data_list:
            row = {
                "Product Title": item.get("Product Title", "N/A"),
                "Product URL": item.get("Product URL", "N/A"),
                "Date Scraped": item.get("Date Scraped", "N/A"),
            }
            # FIXED: Use Key Attributes instead of Attributes
            attributes = item.get("Key Attributes", {})
            for key in all_attr_keys:
                row[key] = attributes.get(key, "N/A")
            writer.writerow(row)
            
            
def save_to_json(data_list, filename):
    """Save data to JSON with corrected key handling"""
    if not data_list:
            print("No data to save.")
            return
        
    try:
        with open(filename, mode="w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)
            print(f"Data successfully saved to {filename}.")
    except Exception as e:
            print(f"Error saving to JSON: {e}")
    
    

# ================== Main Workflow ==================

def main():
    driver = init_driver()
    
    # 1. Open Alibaba search
    search_url = f"https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&SearchText=puff+panels"
    driver.get(search_url)
    
    scraped_data = []
    
    # 2. Find products with improved waiting
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".search-card-e-title"))
    )
    product_elements = driver.find_elements(By.CSS_SELECTOR, ".search-card-e-title span")
    total_products = len(product_elements)
    print(f"Found {total_products} products")
    
    # 3. Product processing loop
    for index in range(total_products):
        try:
            # FIXED: Re-fetch elements after every navigation
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".search-card-e-title span"))
            )
            current_products = driver.find_elements(By.CSS_SELECTOR, ".search-card-e-title span")
            
            if index >= len(current_products):
                print(f"Stopped at index {index}")
                break
                
            product = current_products[index]
            print(f"Processing {index+1}/{total_products}: {product.text[:30]}...")
            
            
            # FIXED: Use JavaScript click to avoid element detachment
            driver.execute_script("arguments[0].click();", product)
            
            # Scrape product page
            product_data = scrape_product_page(driver)
            scraped_data.append(product_data)
            
            # FIXED: Proper tab handling
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            
            # Wait for search results reload
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".search-card-e-title"))
            )
            
        except Exception as e:
            print(f"Failed on product {index+1}: {str(e)[:100]}")
            # Reset to search page
            while len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            driver.get(search_url)
            time.sleep(5)

    # 4. Save results
    save_to_csv(scraped_data, "alibaba_puff_panels.csv")
    save_to_json(scraped_data, "alibaba_puff_panels.json")
    driver.quit()

if __name__ == "__main__":
    main()
