import os, asyncio, io, requests, time
from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '')
PAIR_ADDRESS = os.getenv('PAIR_ADDRESS', '')
CHAIN = os.getenv('CHAIN', 'BSC')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID', '@lunacatofficialGroup')

def get_font(size, bold=True):
    # Try common paths first, then Pillow default with size
    paths = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf', 'DejaVuSans-Bold.ttf']
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def generate_buy_card(usd, amount, buyer, price, mcap):
    W, H = 1000, 1250
    img = Image.new('RGB', (W, H), (255, 200, 0))
    draw = ImageDraw.Draw(img)
    f_title = get_font(52, True)
    f_tier = get_font(68, True)
    f_amount = get_font(62, True)
    f_info = get_font(44, True)
    f_small = get_font(38, False)
    if usd < 1:
        tier = 'SMALL BUY'
    elif usd <= 5:
        tier = 'MEDIUM BUY'
    elif usd < 50:
        tier = 'LARGE BUY'
    else:
        tier = 'BIG BUY'
    # Top bar
    draw.rectangle([0, 0, W, 140], fill=(0,0,0))
    draw.text((W//2, 70), 'LUNACAT BUY ALERT', fill=(255,200,0), font=f_title, anchor='mm')
    # Cat circle - try to load logo, else draw cat face
    draw.ellipse([330, 180, 670, 520], fill=(255,255,255), outline=(0,0,0), width=6)
    logo_loaded = False
    for logo_path in ['lunacat_logo.jpg', 'lunacat_logo.png', 'logo.jpg', 'logo.png']:
        try:
            logo = Image.open(logo_path).convert('RGB')
            # crop to square and resize to fit circle
            w, h = logo.size
            s = min(w, h)
            logo = logo.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))
            logo = logo.resize((300, 300))
            # circular mask
            mask = Image.new('L', (300, 300), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse([0, 0, 300, 300], fill=255)
            img.paste(logo, (350, 200), mask)
            logo_loaded = True
            break
        except Exception:
            continue
    if not logo_loaded:
        # fallback: draw simple cute cat face
        draw.ellipse([410, 280, 470, 340], fill=(0,0,0))
        draw.ellipse([530, 280, 590, 340], fill=(0,0,0))
        draw.arc([420, 360, 580, 450], 0, 180, fill=(0,0,0), width=6)
        draw.text((W//2, 470), 'LUNACAT', fill=(0,0,0), font=f_title, anchor='mm')
    # Tier bar
    draw.rectangle([40, 560, 960, 680], fill=(0,0,0))
    draw.text((W//2, 620), tier + '  $' + format(usd, '.2f'), fill=(255,200,0), font=f_tier, anchor='mm')
    # White box
    draw.rounded_rectangle([40, 710, 960, 1120], radius=28, fill=(255,255,255))
    draw.text((W//2, 790), format(amount, ',.0f') + ' LUNACAT', fill=(230,160,0), font=f_amount, anchor='mm')
    draw.text((W//2, 890), 'Buyer: ' + buyer, fill=(0,0,0), font=f_info, anchor='mm')
    draw.text((W//2, 970), 'Price: $' + str(price), fill=(0,0,0), font=f_info, anchor='mm')
    draw.text((W//2, 1050), 'Market Cap: $' + str(mcap), fill=(0,0,0), font=f_info, anchor='mm')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

async def send_buy_alert_to(app, chat_id, buy):
    usd = buy['usd']; amount = buy['amount']; buyer = buy['buyer']; price = buy['price']; mcap = buy['mcap']
    caption = 'LUNACAT BUY ALERT\n\nBought: $' + format(usd, '.2f') + '\nAmount: ' + format(amount, ',.0f') + ' $LUNACAT\nBuyer: ' + buyer + '\nPrice: $' + str(price) + '\nMarket Cap: $' + str(mcap) + '\n\nLUNACAT TO THE MOON!'
    keyboard = [[InlineKeyboardButton('Chart', url='https://dexscreener.com'), InlineKeyboardButton('Buy', url='https://t.me/lunacatofficialGroup'), InlineKeyboardButton('Group', url='https://t.me/lunacatofficialGroup')]]
    try:
        photo = generate_buy_card(usd, amount, buyer, price, mcap)
        await app.bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
        return True
    except Exception as e:
        print('photo error', e)
        await app.bot.send_message(chat_id=chat_id, text=caption, reply_markup=InlineKeyboardMarkup(keyboard))
        return False

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
    ok = await send_buy_alert_to(context.application, update.effective_chat.id, fake)
    if ok:
        await update.message.reply_text('Yan yung bagong card - malaki na text!')
    else:
        await update.message.reply_text('Photo failed, text lang muna.')
    try:
        await send_buy_alert_to(context.application, GROUP_CHAT_ID, fake)
    except Exception as e:
        print('group send failed', e)

async def settings(update, context):
    await update.message.reply_text('LUNACAT Settings\n\nMin Buy: $0.10\nMode: 24/7 Auto\nCheck every: 10 seconds\nChain: ' + CHAIN)

seen_hashes = set()
async def get_price_usd():
    # Use GeckoTerminal API - works for pairs from GeckoTerminal, even if Dexscreener has no pair
    try:
        r = requests.get('https://api.geckoterminal.com/api/v2/networks/bsc/pools/' + PAIR_ADDRESS, timeout=10, headers={'Accept': 'application/json'})
        print('GeckoTerminal status:', r.status_code, 'len:', len(r.text))
        if r.status_code == 429:
            print('GeckoTerminal RATE LIMIT - waiting 30s, using last price')
            return 0, '0'
        if r.status_code == 200 and r.text.strip():
            j = r.json()
            attr = j.get('data', {}).get('attributes', {})
            price = attr.get('base_token_price_usd', 0) or 0
            # base_token is LUNACAT if pool is LUNACAT/WBNB, check
            print('GeckoTerminal price:', price, 'FDV:', attr.get('fdv_usd', '0'), 'Pool:', attr.get('name',''))
            return float(price or 0), str(attr.get('fdv_usd', '0'))
        else:
            print('GeckoTerminal raw:', r.text[:300])
    except Exception as e:
        print('Gecko price error', e)
    # Fallback Dexscreener token
    try:
        r = requests.get('https://api.dexscreener.com/latest/dex/tokens/' + CONTRACT_ADDRESS, timeout=10)
        if r.status_code == 429:
            print('GeckoTerminal RATE LIMIT - waiting 30s, using last price')
            return 0, '0'
        if r.status_code == 200 and r.text.strip():
            pairs = r.json().get('pairs') or []
            for p in pairs:
                if float(p.get('priceUsd', 0) or 0) > 0:
                    return float(p.get('priceUsd', 0) or 0), str(p.get('fdv', '0'))
    except Exception as e:
        print('Dex fallback error', e)
    return 0, '0'
async def poll_loop(app):
    print('LUNACAT REAL MONITOR STARTED - BscScan + Dexscreener - Min $0.10')
    global seen_hashes
    bsc_key = os.getenv('BSCSCAN_API_KEY', 'YourApiKeyToken')
    # init seen hashes to avoid spamming old buys on first start
    try:
        r = requests.get('https://api.etherscan.io/v2/api?chainid=56&module=account&action=tokentx&contractaddress=' + CONTRACT_ADDRESS + '&page=1&offset=20&sort=desc&apikey=' + bsc_key, timeout=10)
        if r.status_code == 200:
            for tx in r.json().get('result', []):
                if isinstance(tx, dict):
                    seen_hashes.add(tx.get('hash',''))
        print('Init seen:', len(seen_hashes))
    except Exception as e:
        print('init error', e)
    while True:
        try:
            if CONTRACT_ADDRESS and PAIR_ADDRESS:
                price, mcap = await get_price_usd()
                print('Check - Price:', price, 'Mcap:', mcap)
                r = requests.get('https://api.etherscan.io/v2/api?chainid=56&module=account&action=tokentx&contractaddress=' + CONTRACT_ADDRESS + '&page=1&offset=20&sort=desc&apikey=' + bsc_key, timeout=15)
                print('BscScan status:', r.status_code, 'len:', len(r.text))
                if not r.text.strip() or r.text.strip().startswith('<'):
                    print('BscScan returned HTML / empty - API Key maybe wrong or rate limit. Raw start:', r.text[:200])
                    continue
                if r.status_code == 200:
                    result = r.json().get('result', [])
                    print('BscScan tx count:', len(result) if isinstance(result, list) else 'not list', 'raw:', str(result)[:500])
                    if isinstance(result, list):
                        for tx in reversed(result):
                            h = tx.get('hash','')
                            if h in seen_hashes:
                                continue
                            seen_hashes.add(h)
                            # Buy = Pair sends LUNACAT to buyer
                            if tx.get('from','').lower() != PAIR_ADDRESS.lower():
                                continue
                            buyer = tx.get('to','')
                            try:
                                amount = float(tx.get('value','0')) / (10 ** int(tx.get('tokenDecimal','18')))
                            except:
                                amount = 0
                            usd = amount * price if price else 0
                            print('NEW BUY FOUND:', buyer, amount, usd)
                            if usd < 0.01:
                                print('Too small, skip', usd)
                                continue
                            buy = {'usd': usd, 'amount': amount, 'buyer': buyer, 'price': str(price), 'mcap': str(mcap)}
                            await send_buy_alert_to(app, GROUP_CHAT_ID, buy)
                            print('Posted to group!')
                else:
                    print('BscScan error', r.status_code)
            else:
                print('Waiting Contract + Pair')
        except Exception as e:
            print('poll error', e)
        await asyncio.sleep(30)

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
