import os
import time
import logging
import threading
import requests
from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 환경 변수 로드
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CMC_API_KEY = os.getenv("CMC_API_KEY")

# 로깅
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename="error.log"
)

CACHE = {"price": None, "timestamp": None}

# 환율 가져오기
def get_usdt_to_krw():
    now = time.time()
    if CACHE["price"] and CACHE["timestamp"] and now - CACHE["timestamp"] < 60:
        return CACHE["price"]
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    parameters = {"symbol": "USDT", "convert": "KRW"}
    headers = {"Accepts": "application/json", "X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        data = response.json()
        price = data["data"]["USDT"]["quote"]["KRW"]["price"]
        CACHE["price"] = price
        CACHE["timestamp"] = now
        return price
    except Exception as e:
        logging.error("Error fetching exchange rate: %s", e)
        return None

# 텔레그램 핸들러
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("안녕하세요! 777 EXCHANGE RATE 봇입니다.\n/help 로 사용법을 확인하세요.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📗 사용법:\n"
        "/price - 현재 USDT <-> KRW 환율을 조회합니다.\n"
        "/help - 사용법을 다시 봅니다."
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_usdt_to_krw()
    if price:
        await update.message.reply_text(f"💱 현재 1 USDT = {price:,.2f} KRW 입니다.")
    else:
        await update.message.reply_text("❌ 환율 정보를 가져오지 못했습니다.")

# Flask 설정
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Flask is running. Telegram bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))  # Render가 자동 할당
    flask_app.run(host="0.0.0.0", port=port)

# Telegram 봇 실행
def run_telegram():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", price))
    print("🤖 Telegram Bot Started...")
    app.run_polling()

# 병렬 실행
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_telegram()
