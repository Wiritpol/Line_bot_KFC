import csv
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Parameters
url = "https://www.kfc.co.th/menu/meals"
filename = "kfc_menu.csv"

# Install ChromeDriver automatically
chromedriver_autoinstaller.install()

# Setup Chrome options
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')  # Enable headless mode if needed

# Start browser
driver = webdriver.Chrome(options=chrome_options)
driver.get(url)

# Accept cookies
try:
    wait = WebDriverWait(driver, 10)
    accept_btn = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
    accept_btn.click()
    print("✅ Accepted cookie popup.")
except Exception as e:
    print("⚠️ No cookie popup found:", e)

# Wait for initial content
time.sleep(3)

# Scroll step-by-step using PAGE_DOWN key
scroll_pause_time = 1
scroll_step = 500  # เลื่อนทีละ 300px
last_height = driver.execute_script("return document.body.scrollHeight")

print("📜 Scrolling gradually...")

while True:
    # เลื่อนลงทีละนิด
    driver.execute_script(f"window.scrollBy(0, {scroll_step});")
    time.sleep(scroll_pause_time)

    # ตรวจสอบความสูงของหน้า
    new_height = driver.execute_script("return window.scrollY + window.innerHeight")
    total_height = driver.execute_script("return document.body.scrollHeight")

    print(f"🌀 Scrolled to {new_height} / {total_height}")

    if new_height >= total_height:
        print("✅ Reached bottom of page.")
        break


# Get page HTML
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Extract menu items
menu_items = [div.get_text(strip=True) for div in soup.find_all("div", class_="small-menu-product-header")]

# Extract image URLs
images = soup.find_all("img", class_="false small-menu-product-image")
image_urls = [urlparse(img.get("src"))._replace(query="").geturl() for img in images]

# Close browser
driver.quit()

# Save to CSV
with open(filename, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Menu Item", "Image URL"])
    for item, image in zip(menu_items, image_urls):
        writer.writerow([item, image])

print(f"✅ Saved {len(menu_items)} menu items to '{filename}'")
