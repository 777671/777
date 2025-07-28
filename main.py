import os
import telebot
import requests
import time
import logging
from flask import Flask, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CMC_API_KEY = os.getenv("CMC_API_KEY")

# Logging setup
logging.basicConfig(level=logging.INFO, filename='error.log', filemode='a', format='%(asctime)s %(levelname)s:%(message)s')

# Bot and Flask
bot = telebot.TeleBot(TOKEN, parse_mode=None)
app = Flask(__name__)

# Exchange rate cache
exchange_cache = {'price': None, 'timestamp': 0}

# 도움말 메시지
HELP_MSG = """📗 777 EXCHANGE RATE 봇 사용법:

• /테더 <숫자>: USDT → 원화 환산
• /원화 <숫자>: 원화 → USDT 환산
• /시세 : 실시간 USDT 시세 보기
• /start, /help : 사용법 보기

※ 모든 명령어는 '/'를 포함해야 합니다"""

# 실시간 시세 가져오기
def get_price():
    try:
        now = time.time()
        if exchange_cache['price'] and now - exchange_cache['timestamp'] < 60:
            return exchange_cache['price']

        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        params = {"symbol": "USDT", "convert": "KRW"}
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        price = data['data']['USDT']['quote']['KRW']['price']
        exchange_cache['price'] = price
        exchange_cache['timestamp'] = now
        return price
    except Exception as e:
        logging.error(f"시세 가져오기 오류: {e}")
        return None

# 텔레그램 명령어 처리
@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    bot.reply_to(message, HELP_MSG)

@bot.message_handler(commands=['시세'])
def send_price(message):
    price = get_price()
    if price:
        bot.reply_to(message, f"💱 현재 USDT 시세: {price:,.2f}원", parse_mode=None)
    else:
        bot.reply_to(message, "❌ 시세를 가져오는 데 실패했습니다.", parse_mode=None)

@bot.message_handler(commands=['테더'])
def usdt_to_krw(message):
    try:
        amount = float(message.text.split()[1])
        price = get_price()
        if price:
            result = amount * price
            bot.reply_to(message, f"💸 {amount} USDT ≈ {result:,.0f} 원", parse_mode=None)
        else:
            raise ValueError("가격 없음")
    except Exception as e:
        logging.error(f"테더 변환 오류: {e}")
        bot.reply_to(message, "❌ 변환 중 오류가 발생했습니다.", parse_mode=None)

@bot.message_handler(commands=['원화'])
def krw_to_usdt(message):
    try:
        amount = float(message.text.split()[1])
        price = get_price()
        if price:
            result = amount / price
            bot.reply_to(message, f"💵 {amount:,.0f} 원 ≈ {result:.2f} USDT", parse_mode=None)
        else:
            raise ValueError("가격 없음")
    except Exception as e:
        logging.error(f"원화 변환 오류: {e}")
        bot.reply_to(message, "❌ 변환 중 오류가 발생했습니다.", parse_mode=None)

# 웹훅용 라우터
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "", 200

# Render에서 실행
if __name__ == "__main__":
    if os.getenv("RENDER") == "true":
        bot.remove_webhook()
        bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    else:
        bot.remove_webhook()
        bot.infinity_polling()
