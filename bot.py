import os
import asyncio
from fastapi import FastAPI, Request
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.constants import ParseMode

# --- Environment Variables ---
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("TOKEN or WEBHOOK_URL not found!")

bot = Bot(TOKEN)
app = FastAPI()

# --- Track user states and who started the bot ---
user_state = {}
started_users = set()

# --- Helper: send temporary message ---
async def send_temp_message(chat_id, text, delay=3, reply_markup=None):
    msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(delay)
    await bot.delete_message(chat_id=chat_id, message_id=msg.message_id)

# --- Helper: auto notification sender ---
async def send_hourly_notifications():
    await asyncio.sleep(100)  # wait a bit for bot startup
    while True:
        if started_users:
            print(f"🔔 Sending hourly notification to {len(started_users)} users...")
            for chat_id in list(started_users):
                try:
                    image_url = "https://i.ibb.co/Qv28pXCH/photo-2025-10-16-12-51-06.jpg"  # Replace with your image URL
                    caption = (
                        "🎉 *Claim Your Bonus Before It’s Gone!*\n\n"
                        "💰  *Just Click and Claim Bonus Now 🩵*\n\n"
                        "We just wanted to remind you that you haven’t claimed your Bonus yet.\n"
                        "Click the button below to claim your exclusive Bonus."
                    )
                    keyboard = [
                        [InlineKeyboardButton("🎁 Claim Bonus", url="https://stakecom.vip/")]
                    ]
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=image_url,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except Exception as e:
                    print(f"❌ Failed to send to {chat_id}: {e}")
        else:
            print("ℹ️ No users to notify yet.")
        await asyncio.sleep(3600)  # change this to adjust auto message frequency

# --- Webhook route ---
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)
    chat_id = None

    # --- Handle user text messages ---
    if update.message:
        chat_id = update.message.chat.id
        text = update.message.text
        state = user_state.get(chat_id, "START")

        # --- /start command ---
        if text.lower() == "/start":
            started_users.add(chat_id)  # save user
            print(f"✅ New user started: {chat_id}")

            # --- Remove all previous bot messages ---
            try:
                me = await bot.get_me()
                async for message in bot.get_chat_history(chat_id, limit=50):
                    if message.from_user and message.from_user.id == me.id:
                        try:
                            await bot.delete_message(chat_id, message.message_id)
                        except:
                            pass
            except Exception as e:
                print("Cleanup error:", e)

            # --- Create bottom menu buttons ---
            bottom_menu = [
                [KeyboardButton("💎 350% Bonus"), KeyboardButton("🎁 Claim Bonus")]
            ]
            reply_markup = ReplyKeyboardMarkup(bottom_menu, resize_keyboard=True)

            # --- Send welcome image and caption ---
            image_url = "https://i.ibb.co/G3VtkMCz/photo-2025-10-16-12-54-30.jpg"  # Replace with your image
            caption = (
                "👋 *Welcome to Stake Exclusive Bot!*\n\n"
                "💎 Get up to *350% Bonus* [Claim here](https://stakecom.vip/)\n"
                "🎟 *Min. Deposit:* $200\n"
                "🎰 *Wager Requirement:* 2x\n\n"
                "🚨 Hurry – Exclusive bonus is only available for a limited time!\n"
                "Don’t miss your chance to win big! 🤑"
            )

            keyboard = [
                [InlineKeyboardButton("🎁 Claim Bonus", url="https://stakecom.vip/")]
            ]

            await bot.send_photo(
                chat_id=chat_id,
                photo=image_url,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup  # show bottom buttons
            )

            user_state[chat_id] = "START"
            return {"ok": True}

        # --- Handle bottom menu button clicks ---
        if text == "💎 350% Bonus" or text == "🎁 Claim Bonus":
            url = "https://stakecom.vip/"  # Change this to your link
            await bot.send_message(
                chat_id=chat_id,
                text=f"👉 Click here to continue: [Open Bonus Page]({url})",
                parse_mode=ParseMode.MARKDOWN
            )

    return {"ok": True}

# --- Webhook setup ---
async def set_webhook():
    url = f"{WEBHOOK_URL}/"
    await bot.delete_webhook()
    await bot.set_webhook(url)
    print(f"✅ Webhook set to {url}")

# --- Background task starter ---
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(send_hourly_notifications())

# --- Main runner ---
if __name__ == "__main__":
    import uvicorn
    asyncio.run(set_webhook())
    uvicorn.run("bot:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
