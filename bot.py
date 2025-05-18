import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# 環境變數
TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", 0))  # 必須是整數
WELCOME_MESSAGE = "👋 各位蒞臨潤匯港的貴賓你好！\n有任何匯率相關的問題，請私訊我，我會盡快為您服務！"

# 啟動 Flask 與 Telegram Bot
app = Flask(__name__)
bot_app = ApplicationBuilder().token(TOKEN).build()

# 暫存對應表：私訊者對應的 message_id
user_to_message = {}

# /start 指令回覆歡迎訊息
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

# 處理來自用戶的私訊並轉發到群組
async def forward_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        sent_msg = await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"來自 {update.effective_user.full_name} 的訊息：\n{update.message.text}",
        )
        user_to_message[sent_msg.message_id] = update.message.chat_id

# 處理來自群組的回覆並轉發給原用戶
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

# 額外 debug：打印所有訊息 chat_id
async def debug_print_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[DEBUG] chat_id: {update.message.chat_id}, user: {update.effective_user.full_name}, text: {update.message.text}")

# 註冊處理器
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, forward_to_group))
bot_app.add_handler(MessageHandler(filters.TEXT & filters.Chat(GROUP_ID), reply_to_user))
bot_app.add_handler(MessageHandler(filters.ALL, debug_print_chat_id))

# Webhook 路由處理（同步，不用 asyncio.create_task）
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put_nowait(update)
    return "ok"

# 執行主程式
if __name__ == "__main__":
    import asyncio

    async def run():
        await bot_app.initialize()
        await bot_app.start()
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)

    asyncio.run(run())



