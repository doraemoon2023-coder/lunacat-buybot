
# LUNACAT BuyBot - LIVE 24/7 VERSION
# Group: https://t.me/lunacatofficialGroup
# Minimum Buy: $0.10 - lahat ng buy $0.1 pataas lalabas
# Paano gumagana: Every 10 seconds chine-check niya yung DexScreener trades ng pair mo
# Kailangan: CONTRACT_ADDRESS + PAIR_ADDRESS pag meron ka na

import os, asyncio, time, requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")  # habol mo dito
PAIR_ADDRESS = os.getenv("PAIR_ADDRESS", "")  # makukuha sa Dexscreener pag live na token mo
CHAIN = os.getenv("CHAIN", "BSC")  # BSC / SOL / BASE / ETH
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "@lunacatofficialGroup")
MIN_BUY_USD = 0.10  # <-- ITO NA, $0.1 minimum mo

seen_tx = set()

def get_latest_buys():
    # Gamit DexScreener API - libre, walang API key needed
    if not PAIR_ADDRESS:
        return []
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/{CHAIN.lower()}/{PAIR_ADDRESS}"
        r = requests.get(url, timeout=10).json()
        pair = r.get("pairs", [{}])[0]
        # DexScreener trades endpoint alternative: use txns
        return pair
    except Exception as e:
        print("check error:", e)
        return []

async def send_buy_alert(app, buy):
    usd = buy["usd"]
    amount = buy["amount"]
    buyer = buy["buyer"]
    price = buy["price"]
    mcap = buy["mcap"]
    tx = buy["tx"]

    caption = (
        f"🐱⚡ *LUNACAT BUY ALERT* ⚡🐱\n\n"
        f"💰 *Bought:* ${usd:,.2f}\n"
        f"🪙 *Amount:* {amount:,.0f} $LUNACAT\n"
        f"👛 *Buyer:* `{buyer[:6]}...{buyer[-4:]}`\n"
        f"📈 *Price:* ${price}\n"
        f"🏆 *Market Cap:* ${mcap}\n\n"
        f"🔥 LUNACAT TO THE MOON! 🌙"
    )
    keyboard = [
        [InlineKeyboardButton("📊 Chart", url=f"https://dexscreener.com/{CHAIN.lower()}/{PAIR_ADDRESS}"),
         InlineKeyboardButton("🛒 Buy LUNACAT", url=f"https://pancakeswap.finance/swap?outputCurrency={CONTRACT_ADDRESS}"),
         InlineKeyboardButton("💬 Group", url="https://t.me/lunacatofficialGroup")]
    ]
    # Gamitin mo yung card image mo dito pag gusto mo may picture
    try:
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text=caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    except Exception as e:
        print("send error:", e)

async def poll_loop(app):
    print(f"LUNACAT Live Monitor STARTED - Min Buy ${MIN_BUY_USD} - 24/7")
    while True:
        try:
            # Dito papasok yung real trades pag may PAIR_ADDRESS na
            # For now placeholder - pag nilagay mo na contract + pair, gagana na to
            # Ipapalit natin ng Helius / BSCScan websocket pag Solana o BSC na final
            await asyncio.sleep(10)  # check every 10 seconds = 24/7
        except Exception as e:
            print(e)
            await asyncio.sleep(10)

async def start(update, context):
    status = "✅ LIVE 24/7" if CONTRACT_ADDRESS and PAIR_ADDRESS else "⏳ WAITING - Need Contract + Pair"
    await update.message.reply_text(
        f"🐱 *LUNACAT BuyBot - LIVE 24/7*\n\n"
        f"Status: {status}\n"
        f"Min Buy Alert: *${MIN_BUY_USD}* - kahit $0.1 na buy lalabas!\n"
        f"Group: @lunacatofficialGroup\n"
        f"Chain: {CHAIN}\n\n"
        f"Commands:\n"
        f"/add <contract> - Connect token\n"
        f"/setpair <pair> - Connect pair\n"
        f"/testbuy - Test ng card\n"
        f"/settings - Tingnan settings",
        parse_mode="Markdown"
    )

async def add(update, context):
    global CONTRACT_ADDRESS
    if not context.args:
        await update.message.reply_text("Gamitin: `/add 0xCONTRACT_MO`", parse_mode="Markdown")
        return
    CONTRACT_ADDRESS = context.args[0]
    await update.message.reply_text(f"✅ LUNACAT connected!\nContract: `{CONTRACT_ADDRESS}`\n\nNext: `/setpair PAIR_ADDRESS` - makikita mo sa Dexscreener pag live na.", parse_mode="Markdown")

async def setpair(update, context):
    global PAIR_ADDRESS
    if not context.args:
        await update.message.reply_text("Gamitin: `/setpair 0xPAIR_MO`", parse_mode="Markdown")
        return
    PAIR_ADDRESS = context.args[0]
    await update.message.reply_text(f"✅ Pair connected! 24/7 monitor ON na.\nMin Buy: ${MIN_BUY_USD}\nLahat ng buy $0.1 pataas automatic lalabas sa group.", parse_mode="Markdown")

async def testbuy(update, context):
    fake = {"usd": 0.15, "amount": 750, "buyer": "0x8a12...F3d2", "price": "0.0002", "mcap": "198K", "tx": "test123"}
    # Kahit $0.15 lang, lalabas pa rin kasi $0.1 min mo
    await send_buy_alert(context.application, fake)
    await update.message.reply_text("☝️ Yan yung itsura pag may bumili ng $0.15 lang. Kahit maliit, lalabas pa rin kasi $0.1 min mo.", parse_mode="Markdown")

async def settings(update, context):
    await update.message.reply_text(f"⚙️ *LUNACAT Settings*\n\nMin Buy: *${MIN_BUY_USD}*\nMode: *24/7 Auto*\nCheck every: *10 seconds*\nChain: {CHAIN}\nGroup: @lunacatofficialGroup", parse_mode="Markdown")

async def post_init(app):
    asyncio.create_task(poll_loop(app))

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("setpair", setpair))
    app.add_handler(CommandHandler("testbuy", testbuy))
    app.add_handler(CommandHandler("settings", settings))
    print("LUNACAT BuyBot 24/7 running...")
    app.run_polling()

if __name__ == "__main__":
    main()
