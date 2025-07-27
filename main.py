import os
import time
import logging
import requests
import re
from flask import Flask
from threading import Thread
import telebot
from dotenv import load_dotenv

# 환경 변수 불러오기
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)

# 로깅 설정
logging.basicConfig(filename='error.log', level=logging.ERROR)

# 환율 캐시
cached_price = None
last_updated = 0
CACHE_DURATION = 300  # 5분

# CoinMarketCap에서 USDT 가격 조회
def get_usdt_price():
    global cached_price, last_updated
    current_time = time.time()
    if cached_price and current_time - last_updated < CACHE_DURATION:
        return cached_price

    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        params = {
            "symbol": "USDT",
            "convert": "KRW"
        }
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": CMC_API_KEY
        }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        price = data["data"]["USDT"]["quote"]["KRW"]["price"]
        cached_price = price
        last_updated = current_time
        return price
    except Exception as e:
        logging.error(f"환율 조회 오류: {e}")
        return None

# /start, /help 명령어 처리
@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    help_text = (
        "📗 777 EXCHANGE RATE 봇 사용법:\n\n"
        "• 테더 <숫자>: USDT → 원화 환산\n"
        "• 원화 <숫자>: 원화 → USDT 환산\n"
        "• /price : 실시간 USDT 가격 보기\n"
        "• /start, /help : 사용법 보기\n\n"
        "※ 명령어 앞에 '/' 없어도 작동합니다!"
    )
    bot.reply_to(message, help_text)

# /price 명령어 처리
@bot.message_handler(commands=['price'])
def send_price(message):
    price = get_usdt_price()
    if price:
        bot.reply_to(message, f"💸 현재 1 USDT = {price:,.2f} KRW")
    else:
        bot.reply_to(message, "❌ 환율 정보를 불러오지 못했습니다.")

# 일반 메시지 처리 (숫자 없는 메시지는 무시)
@bot.message_handler(func=lambda message: True)
def convert_currency(message):
    text = message.text.strip().replace(",", "").upper()

    # 숫자가 포함되지 않은 메시지는 무시
    if not re.search(r'\d', text):
        return

    try:
        if "USDT" in text or "테더" in text:
            amount = float(''.join(c for c in text if c.isdigit() or c == '.'))
            rate = get_usdt_price()
            if rate:
                result = amount * rate
                bot.reply_to(message, f"💰 {amount} USDT ≈ {result:,.0f} KRW")
            else:
                bot.reply_to(message, "❌ 환율 정보를 불러오지 못했습니다.")

        elif "KRW" in text or "원화" in text or "원" in text:
            amount = float(''.join(c for c in text if c.isdigit() or c == '.'))
            rate = get_usdt_price()
            if rate:
                result = amount / rate
                bot.reply_to(message, f"💵 {amount:,.0f} KRW ≈ {result:.2f} USDT")
            else:
                bot.reply_to(message, "❌ 환율 정보를 불러오지 못했습니다.")

        else:
            send_help(message)

    except Exception as e:
        logging.error(f"메시지 처리 오류: {e}")
        bot.reply_to(message, "⚠️ 숫자를 포함한 메시지를 입력해 주세요.")

# Flask 서버로 Replit/Render 24시간 실행 유지
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# 메인 실행
if __name__ == '__main__':
    keep_alive()
    print("🤖 환율 봇 실행 중...")
    bot.infinity_polling()
