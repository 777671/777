import os
import telebot
import requests
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("COINMARKETCAP_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 환율 캐싱
exchange_rate_cache = {
    "rate": None,
    "timestamp": 0
}

HELP_TEXT = """📗 777 EXCHANGE RATE 봇 사용법:

• /테더 <숫자>: USDT → 원화 환산
• /원화 <숫자>: 원화 → USDT 환산
• /시세 : 실시간 USDT 시세 보기
• /start, /help : 사용법 보기

※ 모든 명령어는 '/'를 포함해야 합니다"""

def get_exchange_rate():
    import time
    now = time.time()
    # 5분마다 갱신
    if exchange_rate_cache["rate"] and now - exchange_rate_cache["timestamp"] < 300:
        return exchange_rate_cache["rate"]

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": "USDT", "convert": "KRW"}
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        krw_price = data["data"]["USDT"]["quote"]["KRW"]["price"]
        rate = round(krw_price, 2)
        exchange_rate_cache["rate"] = rate
        exchange_rate_cache["timestamp"] = now
        return rate
    except Exception as e:
        print(f"ERROR: 환율 조회 실패: {e}")
        return None

@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    bot.reply_to(message, HELP_TEXT)

@bot.message_handler(commands=['시세'])
def send_rate(message):
    rate = get_exchange_rate()
    if rate:
        bot.reply_to(message, f"💸 현재 USDT 시세: {rate:,.2f}원")
    else:
        bot.reply_to(message, "❌ 시세 정보를 불러오지 못했습니다.")

@bot.message_handler(commands=['테더'])
def convert_to_krw(message):
    try:
        amount = float(message.text.split()[1])
        rate = get_exchange_rate()
        if rate:
            result = round(amount * rate, 2)
            bot.reply_to(message, f"{amount} USDT → {result:,.2f} 원")
        else:
            bot.reply_to(message, "❌ 환율 정보를 불러오지 못했습니다.")
    except Exception as e:
        print(f"ERROR: 테더 변환 오류: {e}")
        bot.reply_to(message, "❌ 변환 중 오류가 발생했습니다.")

@bot.message_handler(commands=['원화'])
def convert_to_usdt(message):
    try:
        amount = float(message.text.split()[1])
        rate = get_exchange_rate()
        if rate:
            result = round(amount / rate, 2)
            bot.reply_to(message, f"{amount:,.0f} 원 → {result} USDT")
        else:
            bot.reply_to(message, "❌ 환율 정보를 불러오지 못했습니다.")
    except Exception as e:
        print(f"ERROR: 원화 변환 오류: {e}")
        bot.reply_to(message, "❌ 변환 중 오류가 발생했습니다.")

# === Flask Webhook Trick (Render Uptime 유지를 위해) ===
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

def run_bot():
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"ERROR: 봇 실행 오류: {e}")

# === 실행 ===
if __name__ == '__main__':
    Thread(target=run_flask).start()
    Thread(target=run_bot).start()
