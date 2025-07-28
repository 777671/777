import os
import logging
import requests
import telebot
import time
from flask import Flask

# 환경 변수 로딩 (Render 환경에서 설정됨)
CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# 유효성 검사
if not TELEGRAM_TOKEN or not CMC_API_KEY:
    raise ValueError("TELEGRAM_TOKEN 또는 CMC_API_KEY가 설정되지 않았습니다.")

# 텔레그램 봇 초기화
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

# 캐시 설정
cache = {}
CACHE_TTL = 10  # 초 단위

# 📗 사용법 텍스트
HELP_TEXT = """📗 777 EXCHANGE RATE 봇 사용법:

• /테더 <숫자>: USDT → 원화 환산
• /원화 <숫자>: 원화 → USDT 환산
• /시세 : 실시간 USDT 시세 보기
• /start, /help : 사용법 보기

※ 모든 명령어는 '/'를 포함해야 합니다"""

# 실시간 시세 가져오기
def get_usdt_krw_price():
    now = int(time.time())
    if 'timestamp' in cache and now - cache['timestamp'] < CACHE_TTL:
        return cache['price']
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {'symbol': 'USDT', 'convert': 'KRW'}
    headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    price = data['data']['USDT']['quote']['KRW']['price']
    cache['timestamp'] = now
    cache['price'] = price
    return price

# /start 또는 /help 명령어 처리
@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    bot.reply_to(message, HELP_TEXT)

# /시세 명령어 처리
@bot.message_handler(commands=['시세'])
def handle_price(message):
    try:
        price = get_usdt_krw_price()
        text = f"💱 실시간 시세: <b>{price:,.2f}₩</b> (1 USDT)"
        bot.reply_to(message, text)
    except Exception as e:
        logger.error("시세 조회 오류: %s", e)
        bot.reply_to(message, "❌ 시세 정보를 가져오는 중 오류가 발생했습니다.")

# /테더 <숫자> : USDT → 원화
@bot.message_handler(commands=['테더'])
def handle_tether(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            return bot.reply_to(message, "❗ 사용법: /테더 <숫자>")
        amount = float(parts[1])
        price = get_usdt_krw_price()
        result = amount * price
        bot.reply_to(message, f"💸 {amount} USDT ≈ <b>{result:,.0f}₩</b>")
    except Exception as e:
        logger.error("테더 변환 오류: %s", e)
        bot.reply_to(message, "❌ 변환 중 오류가 발생했습니다.")

# /원화 <숫자> : 원화 → USDT
@bot.message_handler(commands=['원화'])
def handle_krw(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            return bot.reply_to(message, "❗ 사용법: /원화 <숫자>")
        amount = float(parts[1])
        price = get_usdt_krw_price()
        result = amount / price
        bot.reply_to(message, f"💵 {amount:,.0f}₩ ≈ <b>{result:.2f} USDT</b>")
    except Exception as e:
        logger.error("원화 변환 오류: %s", e)
        bot.reply_to(message, "❌ 변환 중 오류가 발생했습니다.")

# 명령어 이외는 무시
@bot.message_handler(func=lambda m: not m.text.startswith('/'))
def ignore_non_command(message):
    pass

# Flask 앱 (Render용)
app = Flask(__name__)

@app.route('/')
def index():
    return "777 EXCHANGE RATE 봇이 실행 중입니다!"

# 진입점
if __name__ == "__main__":
    from threading import Thread

    def run_bot():
        logger.info("🤖 Telegram 봇 시작됨")
        bot.infinity_polling()

    def run_web():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

    Thread(target=run_bot).start()
    Thread(target=run_web).start()
