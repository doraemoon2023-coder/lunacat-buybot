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


def format_price(p):
    try:
        v = float(p)
    except:
        return str(p)
    if v == 0:
        return '0'
    if v >= 1:
        # $8, $32 style - no decimals if whole
        if v == int(v):
            return str(int(v))
        return ('%.2f' % v).rstrip('0').rstrip('.')
    if v >= 0.01:
        return ('%.4f' % v).rstrip('0').rstrip('.')
    # Tiny price like 0.0000000736 -> show 2 significant digits: 0.000000074
    # Format to 8 decimals max, strip zeros
    s = ('%.8f' % v).rstrip('0').rstrip('.')
    return s

def format_mcap(m):
    try:
        v = float(m)
    except:
        return str(m)
    if v == 0:
        return '0'
    if v >= 1000000:
        return ('%.1f' % (v/1000000)).rstrip('0').rstrip('.') + 'M'
    if v >= 1000:
        return ('%.1f' % (v/1000)).rstrip('0').rstrip('.') + 'K'
    # $30.9233 -> $31, $38.78 -> $39
    return str(int(round(v)))

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
    draw.text((W//2, 890), 'Buyer: ' + buyer[:6] + '...' + buyer[-4:] if len(buyer) > 12 else 'Buyer: ' + buyer, fill=(0,0,0), font=f_info, anchor='mm')
    draw.text((W//2, 970), 'Price: $' + format_price(price), fill=(0,0,0), font=f_info, anchor='mm')
    draw.text((W//2, 1050), 'Market Cap: $' + format_mcap(mcap), fill=(0,0,0), font=f_info, anchor='mm')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

async def send_buy_alert_to(app, chat_id, buy):
    usd = buy['usd']; amount = buy['amount']; buyer = buy['buyer']; price = buy['price']; mcap = buy['mcap']
    caption = 'LUNACAT BUY ALERT\n\nBought: $' + format(usd, '.2f') + '\nAmount: ' + format(amount, ',.0f') + ' $LUNACAT\nBuyer: ' + buyer + '\nPrice: $' + format_price(price) + '\nMarket Cap: $' + format_mcap(mcap) + '\n\nLUNACAT TO THE MOON!'
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
    # Use Dexscreener for price (different API, so Gecko not rate-limited)
    try:
        r = requests.get('https://api.dexscreener.com/latest/dex/tokens/' + CONTRACT_ADDRESS, timeout=10)
        if r.status_code == 200 and r.text.strip():
            pairs = r.json().get('pairs') or []
            for p in pairs:
                if p.get('pairAddress','').lower() == PAIR_ADDRESS.lower():
                    return float(p.get('priceUsd', 0) or 0), str(p.get('fdv', '0'))
            for p in pairs:
                if float(p.get('priceUsd', 0) or 0) > 0:
                    return float(p.get('priceUsd', 0) or 0), str(p.get('fdv', '0'))
    except Exception as e:
        print('Dex price error', e)
    # Fallback Gecko price only if Dex fails (1 call, cached)
    try:
        r = requests.get('https://api.geckoterminal.com/api/v2/networks/bsc/pools/' + PAIR_ADDRESS, timeout=10, headers={'Accept': 'application/json'})
        if r.status_code == 200 and r.text.strip():
            attr = r.json().get('data', {}).get('attributes', {})
            return float(attr.get('base_token_price_usd', 0) or 0), str(attr.get('fdv_usd', '0'))
    except Exception as e:
        print('Gecko price fallback error', e)
    return 0, '0'
seen_hashes = set()
async def get_price_usd():
    try:
        r = requests.get('https://api.dexscreener.com/latest/dex/tokens/' + CONTRACT_ADDRESS, timeout=10)
        if r.status_code == 200 and r.text.strip():
            pairs = r.json().get('pairs') or []
            for p in pairs:
                if p.get('pairAddress','').lower() == PAIR_ADDRESS.lower():
                    return float(p.get('priceUsd', 0) or 0), str(p.get('fdv', '0'))
            for p in pairs:
                if float(p.get('priceUsd', 0) or 0) > 0:
                    return float(p.get('priceUsd', 0) or 0), str(p.get('fdv', '0'))
    except Exception as e:
        print('Dex price error', e)
    try:
        r = requests.get('https://api.geckoterminal.com/api/v2/networks/bsc/pools/' + PAIR_ADDRESS, timeout=10, headers={'Accept': 'application/json'})
        if r.status_code == 200 and r.text.strip():
            attr = r.json().get('data', {}).get('attributes', {})
            return float(attr.get('base_token_price_usd', 0) or 0), str(attr.get('fdv_usd', '0'))
    except Exception as e:
        print('Gecko price fallback error', e)
    return 0, '0'
seen_hashes = set()
last_block = 0
async def get_price_usd():
    try:
        r = requests.get('https://api.dexscreener.com/latest/dex/tokens/' + CONTRACT_ADDRESS, timeout=10)
        if r.status_code == 200 and r.text.strip():
            pairs = r.json().get('pairs') or []
            for p in pairs:
                if p.get('pairAddress','').lower() == PAIR_ADDRESS.lower():
                    return float(p.get('priceUsd', 0) or 0), str(p.get('fdv', '0'))
            for p in pairs:
                if float(p.get('priceUsd', 0) or 0) > 0:
                    return float(p.get('priceUsd', 0) or 0), str(p.get('fdv', '0'))
    except Exception as e:
        print('Dex price error', e)
    try:
        r = requests.get('https://api.geckoterminal.com/api/v2/networks/bsc/pools/' + PAIR_ADDRESS, timeout=10, headers={'Accept': 'application/json'})
        if r.status_code == 200 and r.text.strip():
            attr = r.json().get('data', {}).get('attributes', {})
            return float(attr.get('base_token_price_usd', 0) or 0), str(attr.get('fdv_usd', '0'))
    except Exception as e:
        print('Gecko price fallback error', e)
    return 0, '0'
def rpc_call(method, params):
    payload = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1}
    r = requests.post('https://bsc-dataseed.binance.org/', json=payload, timeout=10)
    return r.json()
async def poll_loop(app):
    print('LUNACAT REAL MONITOR V20 - BSC RPC DIRECT - REAL-TIME 15s - No BscScan, No Gecko trades')
    global seen_hashes, last_block
    # Get current block
    try:
        res = rpc_call('eth_blockNumber', [])
        last_block = int(res.get('result', '0x0'), 16)
        print('Starting from block:', last_block)
    except Exception as e:
        print('RPC init error', e)
        last_block = 0
    # Transfer topic: 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
    transfer_topic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    # Pair address padded as topic for FROM = Pair (buy)
    pair_topic = '0x000000000000000000000000' + PAIR_ADDRESS[2:].lower()
    while True:
        try:
            if CONTRACT_ADDRESS and PAIR_ADDRESS:
                price, mcap = await get_price_usd()
                print('Check - Price:', price, 'Mcap:', mcap, 'Block:', last_block)
                # Get latest block
                try:
                    res = rpc_call('eth_blockNumber', [])
                    latest = int(res.get('result', '0x0'), 16)
                except Exception as e:
                    print('RPC block error', e)
                    latest = last_block
                if latest > last_block:
                    from_block = hex(last_block + 1)
                    to_block = hex(latest)
                    # Get Transfer logs where FROM = Pair (buy) and contract = LUNACAT
                    try:
                        logs_res = rpc_call('eth_getLogs', [{'fromBlock': from_block, 'toBlock': to_block, 'address': CONTRACT_ADDRESS, 'topics': [transfer_topic, pair_topic]}])
                        logs = logs_res.get('result', []) or []
                        print('RPC logs count:', len(logs), 'blocks:', last_block, '->', latest)
                        for log in logs:
                            tx_hash = log.get('transactionHash', '')
                            if not tx_hash or tx_hash in seen_hashes:
                                continue
                            seen_hashes.add(tx_hash)
                            # topics[2] = TO (buyer), data = amount (hex)
                            try:
                                to_topic = log.get('topics', [])[2] if len(log.get('topics', [])) > 2 else ''
                                buyer = '0x' + to_topic[-40:] if to_topic else ''
                                amount_hex = log.get('data', '0x0')
                                amount_raw = int(amount_hex, 16)
                                amount = amount_raw / (10 ** 18)
                            except Exception as e:
                                print('Decode error', e)
                                continue
                            usd = amount * price if price else 0
                            print('NEW BUY via RPC:', tx_hash[:10], 'USD:', usd, 'Amount:', amount, 'Buyer:', buyer[:10])
                            if usd < 0.10:
                                print('Too small skip', usd)
                                continue
                            buy = {'usd': usd, 'amount': amount, 'buyer': buyer, 'price': str(price), 'mcap': str(mcap)}
                            await send_buy_alert_to(app, GROUP_CHAT_ID, buy)
                            print('Posted to group via RPC!')
                    except Exception as e:
                        print('RPC logs error', e)
                    last_block = latest
                else:
                    print('No new blocks, waiting')
            else:
                print('Waiting Contract + Pair')
        except Exception as e:
            print('poll error', e)
        await asyncio.sleep(15)
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
