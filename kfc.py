import time
from bs4 import BeautifulSoup
from selenium import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse


# Auto-install compatible ChromeDriver
chromedriver_autoinstaller.install()


# Setup Chrome options (uncomment headless if you want no browser UI)
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument('--headless')
#chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('--disable-dev-shm-usage')


# Initialize the WebDriver
driver = webdriver.Chrome(options=chrome_options)


# Target URL
url = "https://www.kfc.co.th/menu/meals"
driver.get(url)


# Wait for page JS to load (adjust if needed)
time.sleep(5)


# Try to accept cookies by clicking the button
try:
    wait = WebDriverWait(driver, 10)
    accept_btn = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
    accept_btn.click()
    print("Clicked the accept cookies button.")
except Exception as e:
    print("Button not found or not clickable:", e)


# Save the page HTML to a file
html = driver.page_source
with open("kfc_menu_page.html", "w", encoding="utf-8") as f:
    f.write(html)


# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')


# Find all divs with class 'small-menu-product-header'
headers = soup.find_all("div", class_="small-menu-product-header")


# Print out menu item titles
print("📋 Menu Item Titles:")
for idx, header in enumerate(headers, 1):
    print(f"{idx}. {header.get_text(strip=True)}")


# Find all img tags with class 'false small-menu-product-image'
images = soup.find_all("img", class_="false small-menu-product-image")


# Print out image URLs
print("\n🖼️ Image URLs:")
for idx, img in enumerate(images, 1):
    img_url = img.get("src")
    parsed_url = urlparse(img_url )
    base_url = parsed_url._replace(query="").geturl()    
    print(f"{idx}. {base_url}")


# Close the browser
driver.quit()
