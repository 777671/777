import telebot
import requests
import os
import time

# 환경 변수에서 토큰 및 API 키 가져오기
TOKEN = os.getenv("TELEGRAM_TOKEN")
CMC_API_KEY = os.getenv("CMC_API_KEY")

if not TOKEN:
    raise Exception("❌ TELEGRAM_TOKEN 환경 변수가 정의되지 않았습니다.")
if not CMC_API_KEY:
    raise Exception("❌ CMC_API_KEY 환경 변수가 정의되지 않았습니다.")

bot = telebot.TeleBot(TOKEN)

# 캐싱: 마지막 환율 및 시간
cached_rate = None
last_updated = 0

# USDT → KRW 환율 가져오기
def get_usdt_to_krw():
    global cached_rate, last_updated
    now = time.time()
    if cached_rate is not None and now - last_updated < 300:
        return cached_rate

    url = "https://pro-api.coinmarketcap.com/v1/tools/price-conversion"
    params = {
        'amount': 1,
        'symbol': 'USDT',
        'convert': 'KRW'
    }
    headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        price = data['data']['quote']['KRW']['price']
        cached_rate = price
        last_updated = now
        return price
    except Exception as e:
        print(f"❌ 환율 조회 오류: {e}")
        return None

# /테더 <금액>
@bot.message_handler(commands=['테더'])
def handle_tether_command(message):
    try:
        amount = float(message.text.split()[1])
        rate = get_usdt_to_krw()
        if rate:
            krw = round(amount * rate, 2)
            bot.reply_to(message, f"💵 {amount} USDT → ￦{krw:,} 원")
        else:
            bot.reply_to(message, "❌ 환율 정보를 가져올 수 없습니다.")
    except:
        bot.reply_to(message, "❗ 사용법: /테더 <숫자>")

# /원화 <금액>
@bot.message_handler(commands=['원화'])
def handle_krw_command(message):
    try:
        amount = float(message.text.split()[1])
        rate = get_usdt_to_krw()
        if rate:
            usdt = round(amount / rate, 2)
            bot.reply_to(message, f"💰 ￦{amount:,} 원 → {usdt} USDT")
        else:
            bot.reply_to(message, "❌ 환율 정보를 가져올 수 없습니다.")
    except:
        bot.reply_to(message, "❗ 사용법: /원화 <숫자>")

# /시세
@bot.message_handler(commands=['시세'])
def handle_price_command(message):
    rate = get_usdt_to_krw()
    if rate:
        bot.reply_to(message, f"💱 현재 1 USDT = ￦{round(rate, 2):,} 원")
    else:
        bot.reply_to(message, "❌ 환율 정보를 가져올 수 없습니다.")

# /start, /help
@bot.message_handler(commands=['start', 'help'])
def handle_help_command(message):
    help_text = (
        "🪙 777 EXCHANGE RATE 봇 사용법:\n\n"
        "• /테더 <숫자>: USDT → 원화 환산\n"
        "• /원화 <숫자>: 원화 → USDT 환산\n"
        "• /시세 : 실시간 USDT 시세 보기\n"
        "• /start, /help : 사용법 보기\n\n"
        "※ 모든 명령어는 '/'를 포함해야 합니다!"
    )
    bot.reply_to(message, help_text)

# 그 외 메시지 무시
@bot.message_handler(func=lambda m: True)
def ignore_non_command(message):
    pass

# 봇 실행
print("✅ 텔레그램 봇 실행 중 (Render용)")
bot.polling(non_stop=True)
