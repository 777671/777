import logging
import requests
import os
import time
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# 환경 변수 불러오기
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CMC_API_KEY = os.getenv("CMC_API_KEY")

# 로그 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename="error.log"
)

# 환율 캐시
CACHE = {"price": None, "timestamp": None}

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

# 텔레그램 봇 명령어
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕하세요! 777 EXCHANGE RATE 봇입니다.\n"
        "/help 를 입력해 사용법을 확인하세요."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📗 777 EXCHANGE RATE 봇 사용법:\n"
        "/price - 현재 USDT <-> KRW 환율을 조회합니다.\n"
        "/help - 사용법을 다시 봅니다."
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_usdt_to_krw()
    if price:
        await update.message.reply_text(f"💱 현재 1 USDT = {price:,.2f} KRW 입니다.")
    else:
        await update.message.reply_text("❌ 환율 정보를 가져오지 못했습니다. 나중에 다시 시도해주세요.")

# 텔레그램 봇 실행 함수
def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", price))
    print("🤖 Telegram Bot Started...")
    app.run_polling()

# Flask 서버 설정 (Render용)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ 777 EXCHANGE RATE 봇이 실행 중입니다."

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# 병렬 실행
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
