from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, CarouselTemplate, CarouselColumn, URIAction, MessageAction
)
import csv
from scrap_detail import open_product_page_by_name_and_get_badge
from bs4 import BeautifulSoup

app = Flask(__name__)

# Your LINE Channel Secret and Access Token
CHANNEL_SECRET = 'xxx'
CHANNEL_ACCESS_TOKEN = 'xxx'



line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Webhook
@app.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# Load KFC menu from CSV
def fetch_kfc_menu_from_csv(csv_path="kfc_menu.csv"):
    menu_items = []

    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                name = row.get("Menu Item")
                image = row.get("Image URL")
                if name and image:
                    menu_items.append({
                        "name": name,
                        "image_url": image
                    })
    except FileNotFoundError:
        print(f"⚠️ CSV file '{csv_path}' not found.")

    return menu_items
def format_badge_text(badge_html):
    soup = BeautifulSoup(badge_html, 'html.parser')
    
    # ลบ HTML tags ที่ไม่จำเป็น
    text = soup.get_text(separator=" ", strip=True)
    
    # จำกัดความยาวของข้อความ (หากข้อความยาวเกินไป)
    if len(text) > 1000:
        text = text[:1000] + "..."

    return text
# Handle messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    print(f"DEBUG: Received message: {user_message}")

    if user_message.lower() == "menu":
        menu_data = fetch_kfc_menu_from_csv()

        if not menu_data:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ No menu data found.")
            )
            return

        menu_data = menu_data[:10]

        carousel_columns = []
        for item in menu_data:
            carousel_columns.append(
                CarouselColumn(
                    thumbnail_image_url=item["image_url"],
                    title=item["name"][:40],
                    text="เมนูแนะนำจาก KFC 🍗",
                    actions=[MessageAction(label="ดูรายละเอียด", text=item["name"])]
                )
            )

        template_message = TemplateSendMessage(
            alt_text="KFC Menu",
            template=CarouselTemplate(columns=carousel_columns)
        )

        line_bot_api.reply_message(event.reply_token, template_message)

    else:
        # Assume user_message is a product name; scrape and reply badge info
        try:
            badge_html, driver = open_product_page_by_name_and_get_badge(user_message)
            driver.quit()  # Close browser after scraping

            # ใช้ฟังก์ชัน format_badge_text เพื่อจัดรูปแบบข้อความ
            badge_text = format_badge_text(badge_html)
            print(f"DEBUG: Processing product: {user_message}") 
            reply_text = f"ข้อมูลเมนู: {user_message}\n{badge_text}"
            print(f"DEBUG: Reply text: {reply_text}")
            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"ไม่พบเมนู '{user_message}' หรือเกิดข้อผิดพลาด: {str(e)}")
            )

if __name__ == "__main__":
    app.run(port=5000)


