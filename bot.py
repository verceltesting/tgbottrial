import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# --- Load environment variables ---
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("TOKEN or WEBHOOK_URL not found!")

bot = Bot(TOKEN)
app = FastAPI()

# --- Track user states ---
user_state = {}

# --- Helper: send disappearing message ---
async def send_temp_message(chat_id, text, delay=3, reply_markup=None):
    msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(delay)
    await bot.delete_message(chat_id=chat_id, message_id=msg.message_id)

# --- Webhook route ---
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)
    chat_id = None

    # --- Handle text messages ---
    if update.message:
        chat_id = update.message.chat.id
        text = update.message.text
        state = user_state.get(chat_id, "START")

        # --- /start command ---
        if text.lower() == "/start":
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

            # --- Send welcome image and caption ---
            image_url = "https://upload.wikimedia.org/wikipedia/commons/f/f2/Felis_silvestris_silvestris_small_gradual_decrease_of_quality_-_JPEG_compression.jpg"  # 🔹 Replace with your image URL
            caption = (
                "👋 *Welcome to Stake Exclusive Bot!*\n\n"
                "💎 Get up to *850% Bonus* [Claim here](https://example.com)\n"
                "🎟 *Min. Deposit:* $200\n"
                "🎰 *Wager Requirement:* 2x\n\n"
                "🚨 Hurry – Exclusive bonus is only available for a limited time!\n"
                "Don’t miss your chance to win big!"
            )

            keyboard = [
                [InlineKeyboardButton("🎁 Claim Bonus", url="https://example.com")]
            ]

            await bot.send_photo(
                chat_id=chat_id,
                photo=image_url,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            user_state[chat_id] = "START"
            return {"ok": True}

       


# --- Set Telegram Webhook ---
async def set_webhook():
    url = f"{WEBHOOK_URL}/"  # Telegram expects full URL
    await bot.delete_webhook()
    await bot.set_webhook(url)
    print(f"✅ Webhook set to {url}")


if __name__ == "__main__":
    import uvicorn
    asyncio.run(set_webhook())
    uvicorn.run("bot:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
