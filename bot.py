import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# 讀取環境變數
TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", 0))
WELCOME_MESSAGE = "\U0001F44B 各位蒞臨潤匯港的貴賓你好！\n有任何匯率相關的問題，請私訊我，我會盡快為您服務！"

# 初始化 Flask 與 Telegram Application
app = Flask(__name__)
bot_app = ApplicationBuilder().token(TOKEN).build()

user_to_message = {}  # 儲存私訊用戶與其轉發訊息的對應

# /start 指令回覆
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

# 私訊 -> 轉發到群組
async def forward_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        sent_msg = await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"來自 {update.effective_user.full_name} 的訊息：\n{update.message.text}",
        )
        user_to_message[sent_msg.message_id] = update.message.chat_id

# 群組回覆 -> 傳回原用戶
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.message.chat_id == GROUP_ID
        and update.message.reply_to_message
        and update.message.reply_to_message.message_id in user_to_message
    ):
        user_id = user_to_message[update.message.reply_to_message.message_id]
        await context.bot.send_message(
            chat_id=user_id,
            text=f"潤匯港客服回覆 : {update.message.text}",
        )

# 顯示 chat_id 用於 debug
async def debug_print_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[DEBUG] chat_id: {update.message.chat_id}, user: {update.effective_user.full_name}, text: {update.message.text}")

# 加入處理器
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, forward_to_group))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.Chat(GROUP_ID), reply_to_user))
bot_app.add_handler(MessageHandler(filters.ALL, debug_print_chat_id))

# Webhook 路由
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def handle():
        await bot_app.update_queue.put(update)

    loop.run_until_complete(handle())
    loop.close()
    return "ok"

# 主程式入口
if __name__ == "__main__":
    async def run():
        await bot_app.initialize()
        await bot_app.start()
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)

    asyncio.run(run())





