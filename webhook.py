from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import time
from bs4 import BeautifulSoup
from selenium import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from linebot.models import (
    TextMessage, TextSendMessage, TemplateSendMessage,
    CarouselTemplate, CarouselColumn, MessageEvent , URIAction
)
app = Flask(__name__)

# Your LINE Channel Secret and Access Token
CHANNEL_SECRET = 'XXX'
CHANNEL_ACCESS_TOKEN = 'XXX'

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Webhook endpoint for LINE to call
@app.route("/", methods=['POST'])
def callback():
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)

    try:
        # Handle the webhook event
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# Event handler for text messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text.lower() == "menu":
        url = "https://www.kfc.co.th/menu/meals"
        result = fetch_kfc_menu(url)

        # Build a carousel message if data exists
        if result["menu_items"] and result["image_urls"]:
            columns = []
            for title, image_url in zip(result["menu_items"], result["image_urls"]):
                # LINE Carousel image limit is 12 columns
                if len(columns) >= 12:
                    break
                column = CarouselColumn(
                    thumbnail_image_url=image_url,
                    title=(title[:40] if len(title) > 40 else title),  # Max 40 characters
                    text="เลือกเพื่อดูรายละเอียด",
                    actions=[
    URIAction(label="ดูเมนู", uri="https://www.kfc.co.th/menu/meals")
]
                )
                columns.append(column)

            carousel_template = CarouselTemplate(columns=columns)
            template_message = TemplateSendMessage(
                alt_text="KFC Menu",
                template=carousel_template
            )
            line_bot_api.reply_message(event.reply_token, template_message)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ขออภัย ไม่สามารถดึงเมนูได้ในขณะนี้")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="กรุณาพิมพ์ 'menu' เพื่อดูเมนู KFC")
        )

def fetch_kfc_menu(url):
    # Auto-install compatible ChromeDriver
    chromedriver_autoinstaller.install()
    # Setup Chrome options (uncomment headless if you want no browser UI)
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')  # Uncomment to run in headless mode
    # Initialize the WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    # Open the URL
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

    # Save the page HTML to a variable
    html = driver.page_source

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find all divs with class 'small-menu-product-header'
    headers = soup.find_all("div", class_="small-menu-product-header")

    # Initialize a list for menu items
    menu_items = []

    for header in headers:
        menu_item = header.get_text(strip=True)
        menu_items.append(menu_item)

    # Find all img tags with class 'false small-menu-product-image'
    images = soup.find_all("img", class_="false small-menu-product-image")

    # Initialize a list for image URLs
    image_urls = []

    for img in images:
        img_url = img.get("src")
        parsed_url = urlparse(img_url)
        base_url = parsed_url._replace(query="").geturl()
        image_urls.append(base_url)

    # Close the browser
    driver.quit()

    # Prepare the result as a dictionary
    result = {
        "menu_items": menu_items,
        "image_urls": image_urls
    }

    return result

if __name__ == "__main__":
    app.run(port=5000)

