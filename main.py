import os
import requests
import time
import logging
from flask import Flask
import telebot
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# 로깅 설정
logging.basicConfig(filename='error.log', level=logging.ERROR)

# 환율 캐시
exchange_cache = {"rate": None, "timestamp": 0}
CACHE_TTL = 60  # 초 단위 캐시 유효 시간

def get_usdt_to_krw():
    try:
        now = time.time()
        if exchange_cache["rate"] and now - exchange_cache["timestamp"] < CACHE_TTL:
            return exchange_cache["rate"]

        url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
        params = {
            "amount": 1,
            "symbol": "USDT",
            "convert": "KRW"
        }
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        rate = data["data"]["quote"]["KRW"]["price"]
        exchange_cache["rate"] = rate
        exchange_cache["timestamp"] = now

        return rate
    except Exception as e:
        logging.error(f"[환율 요청 오류] {e}")
        return None

# 사용법 안내 텍스트
HELP_TEXT = (
    "📗 777 EXCHANGE RATE 봇 사용법:\n\n"
    "• /테더 <숫자>: USDT → 원화 환산\n"
    "• /원화 <숫자>: 원화 → USDT 환산\n"
    "• /시세 : 실시간 USDT 시세 보기\n"
    "• /start, /help : 사용법 보기\n\n"
    "※ 모든 명령어는 '/'를 포함해야 합니다!"
)

@bot.message_handler(commands=["start", "help"])
def send_help(message):
    bot.send_message(message.chat.id, HELP_TEXT)

@bot.message_handler(commands=["시세"])
def send_price(message):
    try:
        rate = get_usdt_to_krw()
        if rate:
            bot.send_message(message.chat.id, f"💵 1 USDT 시세 ≈ 🇰🇷 {rate:,.0f} KRW")
        else:
            bot.send_message(message.chat.id, "❌ 환율 정보를 가져올 수 없습니다.")
    except Exception as e:
        logging.error(f"[시세 처리 오류] {e}")
        bot.send_message(message.chat.id, "❌ 처리 중 오류가 발생했습니다.")

@bot.message_handler(commands=["테더"])
def convert_usdt_to_krw(message):
    try:
        rate = get_usdt_to_krw()
        if not rate:
            bot.send_message(message.chat.id, "❌ 환율 정보를 가져올 수 없습니다.")
            return

        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❗ 사용법: /테더 <숫자>")
            return

        amount = float(parts[1].replace(",", ""))
        result = amount * rate
        bot.send_message(message.chat.id, f"💵 {amount} USDT ≈ 🇰🇷 {result:,.0f} KRW")
    except Exception as e:
        logging.error(f"[테더 변환 오류] {e}")
        bot.send_message(message.chat.id, "❌ 숫자 입력 형식을 확인해 주세요.")

@bot.message_handler(commands=["원화"])
def convert_krw_to_usdt(message):
    try:
        rate = get_usdt_to_krw()
        if not rate:
            bot.send_message(message.chat.id, "❌ 환율 정보를 가져올 수 없습니다.")
            return

        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❗ 사용법: /원화 <숫자>")
            return

        amount = float(parts[1].replace(",", ""))
        result = amount / rate
        bot.send_message(message.chat.id, f"🇰🇷 {amount:,.0f} KRW ≈ 💵 {result:.2f} USDT")
    except Exception as e:
        logging.error(f"[원화 변환 오류] {e}")
        bot.send_message(message.chat.id, "❌ 숫자 입력 형식을 확인해 주세요.")

# 일반 텍스트는 무시 (명령어만 처리)
# 따라서 슬래시 없는 입력은 반응하지 않음

# Flask 서버 (UptimeRobot용 ping)
@app.route('/')
def home():
    return "봇이 실행 중입니다."

# 텔레그램 봇 실행
def start_bot():
    bot.polling(non_stop=True)

if __name__ == "__main__":
    from threading import Thread
    Thread(target=start_bot).start()
    app.run(host="0.0.0.0", port=8080)
