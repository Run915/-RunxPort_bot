from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

TOKEN = os.getenv('TOKEN')
WELCOME_MESSAGE = os.getenv('WELCOME_MESSAGE', '👋 各位蒞臨潤匯港的貴賓你好！\n有任何匯率相關的問題，請私訊我，我會盡快為您服務！')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
