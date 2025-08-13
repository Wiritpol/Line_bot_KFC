from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import chromedriver_autoinstaller
import time
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_chrome_driver(headless=True):
    """Setup Chrome driver with optimized options"""
    chromedriver_autoinstaller.install()
    
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    return webdriver.Chrome(options=chrome_options)

def wait_for_page_load(driver, timeout=10):
    """Wait for page to fully load"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)  # Additional wait for dynamic content
    except TimeoutException:
        logger.warning("Page load timeout, proceeding anyway")

def handle_cookie_popup(driver):
    """Handle cookie acceptance popup"""
    try:
        cookie_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        cookie_button.click()
        logger.info("Cookie popup accepted")
        time.sleep(1)
    except TimeoutException:
        logger.info("No cookie popup found or already accepted")
    except Exception as e:
        logger.warning(f"Error handling cookie popup: {str(e)}")

def find_product_element(driver, product_name, timeout=15):
    """Find product element with multiple search strategies"""
    search_strategies = [
        # Exact match
        f"//div[contains(@class,'menu-product-header') and normalize-space(text())='{product_name}']",
        # Case insensitive
        f"//div[contains(@class,'menu-product-header') and translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{product_name.lower()}']",
        # Contains match
        f"//div[contains(@class,'menu-product-header') and contains(normalize-space(text()), '{product_name}')]",
        # Alternative class names
        f"//h3[contains(@class,'product-title') and contains(normalize-space(text()), '{product_name}')]",
        f"//div[contains(@class,'product-name') and contains(normalize-space(text()), '{product_name}')]"
    ]
    
    for i, xpath in enumerate(search_strategies, 1):
        try:
            logger.info(f"Trying search strategy {i} for product: {product_name}")
            element = WebDriverWait(driver, timeout if i == 1 else 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            logger.info(f"Found product using strategy {i}")
            return element
        except TimeoutException:
            continue
    
    raise TimeoutException(f"Product '{product_name}' not found with any search strategy")

def extract_product_info(driver):
    """Extract product information from detail page"""
    product_info = {
        'badge_text': '',
        'price': '',
        'description': '',
        'ingredients': '',
        'nutrition_info': ''
    }
    
    try:
        # Wait for page to load
        wait_for_page_load(driver)
        
        # Extract badge/tag information
        try:
            badge_elements = driver.find_elements(By.CLASS_NAME, "textbadgecontainer")
            if not badge_elements:
                # Try alternative selectors
                badge_elements = driver.find_elements(By.CSS_SELECTOR, ".badge, .tag, .label, [class*='badge'], [class*='tag']")
            
            if badge_elements:
                badge_texts = []
                for badge in badge_elements:
                    text = badge.text.strip()
                    if text:
                        badge_texts.append(text)
                product_info['badge_text'] = ' | '.join(badge_texts)
                logger.info(f"Found badges: {product_info['badge_text']}")
        except Exception as e:
            logger.warning(f"Error extracting badges: {str(e)}")
        
        # Extract price
        try:
            price_selectors = [
                ".price",
                "[class*='price']",
                ".product-price",
                "[data-testid*='price']"
            ]
            
            for selector in price_selectors:
                price_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for price_elem in price_elements:
                    price_text = price_elem.text.strip()
                    if price_text and ('₿' in price_text or 'บาท' in price_text or price_text.replace('.', '').replace(',', '').isdigit()):
                        product_info['price'] = price_text
                        break
                if product_info['price']:
                    break
        except Exception as e:
            logger.warning(f"Error extracting price: {str(e)}")
        
        # Extract description
        try:
            desc_selectors = [
                ".product-description",
                "[class*='description']",
                ".product-detail",
                "[class*='detail']"
            ]
            
            for selector in desc_selectors:
                desc_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for desc_elem in desc_elements:
                    desc_text = desc_elem.text.strip()
                    if desc_text and len(desc_text) > 20:  # Meaningful description
                        product_info['description'] = desc_text[:200]  # Limit length
                        break
                if product_info['description']:
                    break
        except Exception as e:
            logger.warning(f"Error extracting description: {str(e)}")
        
        # Extract ingredients if available
        try:
            ingredient_keywords = ['ingredient', 'ส่วนประกอบ', 'วัตถุดิบ']
            for keyword in ingredient_keywords:
                elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')]")
                for elem in elements:
                    text = elem.text.strip()
                    if text and len(text) > 10:
                        product_info['ingredients'] = text[:150]
                        break
                if product_info['ingredients']:
                    break
        except Exception as e:
            logger.warning(f"Error extracting ingredients: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error extracting product information: {str(e)}")
    
    return product_info

def clean_text(text):
    """Clean and format extracted text"""
    if not text:
        return ""
    
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep Thai characters
    text = re.sub(r'[^\w\s\u0E00-\u0E7F.,!?()-]', '', text)
    
    return text.strip()

def format_product_info(product_info, product_name):
    """Format product information for display"""
    formatted_parts = []
    
    # Format badge/components information
    if product_info.get('badge_text'):
        badge_text = clean_text(product_info['badge_text'])
        
        # Split components and format nicely
        components = []
        
        # Check if badge_text contains | separator (which is already parsed correctly)
        if '|' in badge_text:
            parts = [part.strip() for part in badge_text.split('|')]
            for part in parts:
                if part:
                    components.append(f"• {part}")
        elif 'PCS.' in badge_text.upper() or 'SIDE ITEM' in badge_text.upper():
            # Split by number patterns and side items
            parts = re.split(r'(?=\d+\s*PCS\.)|(?=SIDE\s*ITEM)', badge_text, flags=re.IGNORECASE)
            
            for part in parts:
                part = part.strip()
                if part:
                    # Clean up component text
                    part = re.sub(r'\s+', ' ', part)
                    components.append(f"• {part}")
        else:
            # Try to split by multiple spaces or other patterns
            if '•' in badge_text:
                parts = badge_text.split('•')
            else:
                # Try to split by multiple spaces
                parts = re.split(r'\s{2,}', badge_text)
            
            for part in parts:
                part = part.strip()
                if part:
                    components.append(f"• {part}")
        
        if components:
            formatted_parts.append("🍗 ในชุดประกอบด้วย:")
            # Join components with line breaks
            formatted_parts.append("\n".join(components))
    
    # Format price (if available)
    if product_info.get('price'):
        price_text = clean_text(product_info['price'])
        if price_text and not 'choose a store' in price_text.lower():
            formatted_parts.append(f"💰 ราคา: {price_text}")
    
    # Format description (clean up generic text)
    if product_info.get('description'):
        desc_text = clean_text(product_info['description'])
        # Remove generic store selection text and product name repetition
        if 'choose a store and order mode' in desc_text.lower():
            desc_parts = desc_text.split('Choose a store')[0].strip()
            # Check if description is just the product name
            if desc_parts and len(desc_parts) > 10 and desc_parts.upper() != product_name.upper():
                formatted_parts.append(f"📝 รายละเอียด: {desc_parts}")
        elif len(desc_text) > 10 and desc_text.upper() != product_name.upper():
            formatted_parts.append(f"📝 รายละเอียด: {desc_text}")
    
    # Format ingredients
    if product_info.get('ingredients'):
        ingredients_text = clean_text(product_info['ingredients'])
        formatted_parts.append(f"🥘 ส่วนประกอบ: {ingredients_text}")
    
    if not formatted_parts:
        return f"พบเมนู '{product_name}' แต่ไม่สามารถดึงข้อมูลรายละเอียดได้"
    
    # Join all parts with double line breaks for better spacing
    return "\n\n".join(formatted_parts)

def open_product_page_by_name_and_get_badge(product_name: str, headless=True):
    """
    Main function to scrape product details from KFC website
    Returns formatted text instead of raw HTML
    """
    driver = None
    try:
        logger.info(f"Starting scrape for product: {product_name}")
        
        # Setup driver
        driver = setup_chrome_driver(headless=headless)
        
        # Navigate to menu page
        menu_url = "https://www.kfc.co.th/menu/meals"
        logger.info(f"Navigating to: {menu_url}")
        driver.get(menu_url)
        
        # Handle cookie popup
        handle_cookie_popup(driver)
        
        # Wait for page to load
        wait_for_page_load(driver)
        
        # Find product element
        name_element = find_product_element(driver, product_name)
        
        # Find product card and get ID
        try:
            product_card = name_element.find_element(By.XPATH, "./ancestor::div[contains(@class,'plp-item-card')]")
            product_id = product_card.get_attribute("id")
            
            if not product_id:
                raise NoSuchElementException("Product ID not found")
                
        except NoSuchElementException:
            # Try alternative method to get product URL
            try:
                product_link = name_element.find_element(By.XPATH, "./ancestor::a | ./following-sibling::a | ./preceding-sibling::a")
                product_url = product_link.get_attribute("href")
            except NoSuchElementException:
                raise Exception(f"Could not find product link for '{product_name}'")
        else:
            # Build product URL from ID
            product_url = f"https://www.kfc.co.th/menu/meals/{product_id}-prod"
        
        logger.info(f"Product URL: {product_url}")
        
        # Navigate to product detail page
        driver.get(product_url)
        
        # Extract product information
        product_info = extract_product_info(driver)
        
        # Format the information
        formatted_info = format_product_info(product_info, product_name)
        
        logger.info("✅ Product information extracted successfully")
        driver.quit()
        return formatted_info, driver
        
    except TimeoutException as e:
        error_msg = f"ไม่พบเมนู '{product_name}' ในระบบ หรือเซิร์ฟเวอร์ตอบสนองช้า"
        logger.error(f"Timeout error: {str(e)}")
        return error_msg, driver
        
    except Exception as e:
        error_msg = f"เกิดข้อผิดพลาดในการค้นหา '{product_name}': {str(e)}"
        logger.error(f"Scraping error: {str(e)}")
        return error_msg, driver