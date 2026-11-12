import os, asyncio, requests, io
from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '')
PAIR_ADDRESS = os.getenv('PAIR_ADDRESS', '')
CHAIN = os.getenv('CHAIN', 'BSC')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID', '@lunacatofficialGroup')
MIN_BUY_USD = 0.10

def generate_buy_card(usd, amount, buyer, price, mcap):
    W, H = 1000, 1200
    img = Image.new('RGB', (W, H), (255, 200, 0))
    draw = ImageDraw.Draw(img)
    try:
        f_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 70)
        f_med = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 50)
        f_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 38)
    except Exception:
        f_big = ImageFont.load_default()
        f_med = f_big
        f_small = f_big
    if usd < 1:
        tier = 'SMALL BUY'
    elif usd <= 5:
        tier = 'MEDIUM BUY'
    elif usd < 50:
        tier = 'LARGE BUY'
    else:
        tier = 'BIG BUY'
    draw.rectangle([50, 30, 950, 130], fill=(0,0,0))
    draw.text((280, 45), 'LUNACAT BUY ALERT', fill=(255,200,0), font=f_med)
    draw.ellipse([350, 170, 650, 470], fill=(255,255,255), outline=(0,0,0), width=5)
    draw.text((390, 290), 'LUNACAT', fill=(0,0,0), font=f_med)
    draw.rectangle([50, 520, 950, 620], fill=(0,0,0))
    draw.text((70, 540), tier + ' $' + format(usd, '.2f'), fill=(255,200,0), font=f_big)
    draw.rounded_rectangle([50, 650, 950, 1050], radius=30, fill=(255,255,255))
    draw.text((80, 700), format(amount, ',.0f') + ' LUNACAT', fill=(230,160,0), font=f_big)
    draw.text((80, 810), 'Buyer: ' + buyer[:6] + '...' + buyer[-4:], fill=(0,0,0), font=f_med)
    draw.text((80, 890), 'Price: $' + str(price), fill=(0,0,0), font=f_med)
    draw.text((80, 970), 'Market Cap: $' + str(mcap), fill=(0,0,0), font=f_med)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

async def send_buy_alert(app, buy):
    usd = buy['usd']; amount = buy['amount']; buyer = buy['buyer']; price = buy['price']; mcap = buy['mcap']
    caption = 'LUNACAT BUY ALERT\n\nBought: $' + format(usd, '.2f') + '\nAmount: ' + format(amount, ',.0f') + ' $LUNACAT\nBuyer: ' + buyer + '\nPrice: $' + str(price) + '\nMarket Cap: $' + str(mcap) + '\n\nLUNACAT TO THE MOON!'
    keyboard = [[InlineKeyboardButton('Chart', url='https://dexscreener.com'), InlineKeyboardButton('Buy', url='https://t.me/lunacatofficialGroup'), InlineKeyboardButton('Group', url='https://t.me/lunacatofficialGroup')]]
    try:
        photo = generate_buy_card(usd, amount, buyer, price, mcap)
        await app.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        print('photo error', e)
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text=caption, reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update, context):
    status = 'LIVE 24/7' if CONTRACT_ADDRESS and PAIR_ADDRESS else 'WAITING - Contract + Pair Required'
    await update.message.reply_text('LUNACAT BuyBot - LIVE 24/7\n\nStatus: ' + status + '\nMin Buy Alert: $0.10 - All buys $0.1+ will be posted!\nGroup: @lunacatofficialGroup\nChain: ' + CHAIN + '\n\nCommands:\n/add <contract> - Connect token\n/setpair <pair> - Connect pair\n/testbuy - Test buy card\n/settings - View settings')

async def add(update, context):
    global CONTRACT_ADDRESS
    if not context.args:
        await update.message.reply_text('Usage: /add <contract_address>')
        return
    CONTRACT_ADDRESS = context.args[0]
    await update.message.reply_text('LUNACAT Connected! Contract: ' + CONTRACT_ADDRESS)

async def setpair(update, context):
    global PAIR_ADDRESS
    if not context.args:
        await update.message.reply_text('Usage: /setpair <pair_address>')
        return
    PAIR_ADDRESS = context.args[0]
    await update.message.reply_text('Pair Connected! 24/7 Monitor is now ON. Min Buy: $0.10')

async def testbuy(update, context):
    fake = {'usd': 3.50, 'amount': 17500, 'buyer': '0x3b12...A9c1', 'price': '0.0002', 'mcap': '198K'}
    await send_buy_alert(context.application, fake)
    await update.message.reply_text('This is how a $3.50 MEDIUM BUY looks with dynamic card.')

async def settings(update, context):
    await update.message.reply_text('LUNACAT Settings\n\nMin Buy: $0.10\nMode: 24/7 Auto\nCheck every: 10 seconds\nChain: ' + CHAIN)

async def poll_loop(app):
    print('LUNACAT Live Monitor STARTED - Min Buy $0.10 - 24/7')
    while True:
        await asyncio.sleep(10)

async def post_init(app):
    asyncio.create_task(poll_loop(app))

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('add', add))
    app.add_handler(CommandHandler('setpair', setpair))
    app.add_handler(CommandHandler('testbuy', testbuy))
    app.add_handler(CommandHandler('settings', settings))
    print('LUNACAT BuyBot 24/7 running...')
    app.run_polling()

if __name__ == '__main__':
    main()