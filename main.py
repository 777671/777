import os
import telebot
import requests
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

cached_price = None

# 시세 조회 함수
def get_usdt_krw_price():
    global cached_price
    try:
        url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
        params = {
            'amount': 1,
            'symbol': 'USDT',
            'convert': 'KRW'
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': CMC_API_KEY
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        price = data['data']['quote']['KRW']['price']
        cached_price = price
        return price
    except Exception as e:
        bot.logger.error(f"시세 조회 오류: {e}")
        return cached_price  # 마지막 성공값 사용

# 📗 봇 도움말
HELP_MSG = (
    "📗 <b>777 EXCHANGE RATE 봇 사용법:</b>\n\n"
    "• <code>/테더 숫자</code>: USDT → 원화 환산\n"
    "• <code>/원화 숫자</code>: 원화 → USDT 환산\n"
    "• <code>/시세</code>: 실시간 USDT 시세 보기\n"
    "• <code>/start</code>, <code>/help</code>: 사용법 보기\n\n"
    "※ 모든 명령어는 '/'를 포함해야 합니다"
)

@bot.message_handler(commands=["start", "help"])
def send_help(message):
    bot.send_message(message.chat.id, HELP_MSG, parse_mode="HTML")

@bot.message_handler(commands=["시세"])
def send_price(message):
    price = get_usdt_krw_price()
    if price:
        bot.send_message(message.chat.id, f"💱 1 USDT = {int(price):,} 원")
    else:
        bot.send_message(message.chat.id, "❌ 시세를 불러오는 데 실패했습니다.")

@bot.message_handler(commands=["테더"])
def convert_usdt_to_krw(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError("잘못된 입력")

        amount = float(parts[1])
        price = get_usdt_krw_price()
        if price:
            result = amount * price
            bot.send_message(message.chat.id, f"💵 {amount} USDT ≈ {int(result):,} 원")
        else:
            bot.send_message(message.chat.id, "❌ 환율 정보를 가져올 수 없습니다.")
    except Exception as e:
        bot.logger.error(f"테더 변환 오류: {e}")
        bot.send_message(message.chat.id, "❌ 변환 중 오류가 발생했습니다.")

@bot.message_handler(commands=["원화"])
def convert_krw_to_usdt(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError("잘못된 입력")

        amount = float(parts[1])
        price = get_usdt_krw_price()
        if price:
            result = amount / price
            bot.send_message(message.chat.id, f"💵 {int(amount):,} 원 ≈ {result:.2f} USDT")
        else:
            bot.send_message(message.chat.id, "❌ 환율 정보를 가져올 수 없습니다.")
    except Exception as e:
        bot.logger.error(f"원화 변환 오류: {e}")
        bot.send_message(message.chat.id, "❌ 변환 중 오류가 발생했습니다.")

# ================================
# 🔁 Render용 Flask 엔드포인트 설정
@app.route("/")
def home():
    return "Bot is alive."

if __name__ == "__main__":
    import threading

    def run_bot():
        bot.remove_webhook()
        bot.infinity_polling()

    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
