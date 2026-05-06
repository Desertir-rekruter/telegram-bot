import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

# ─── Настройки ────────────────────────────────────────────────────────────────

BOT_TOKEN = "8466854890:AAHcnZMW-fVBRtIF51iagGhgFyZhtdiHl4s"           # Получить у @BotFather
SPREADSHEET_ID = "12SY54Kvfrwy6hpinrOyPBK7BZ29ptwrMxVzeozcJ2JY"      # Из URL таблицы Google
CREDENTIALS_FILE = "credentials.json"   # Файл ключей от Google

# ─── Шаги анкеты ──────────────────────────────────────────────────────────────

NAME, PHONE, EMAIL, AGE, COMMENT = range(5)

# ─── Google Sheets ────────────────────────────────────────────────────────────

def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

def save_to_sheet(data: dict):
    sheet = get_sheet()
    # Добавляем заголовки если таблица пустая
    if sheet.row_count == 0 or not sheet.row_values(1):
        sheet.append_row(["Имя", "Телефон", "Email", "Возраст", "Комментарий", "Username", "User ID"])
    sheet.append_row([
        data.get("name", ""),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("age", ""),
        data.get("comment", ""),
        data.get("username", ""),
        data.get("user_id", ""),
    ])

# ─── Хендлеры бота ────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Привет! Я помогу заполнить анкету.\n\n"
        "Введите ваше *имя*:",
        parse_mode="Markdown"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📞 Введите ваш *телефон*:", parse_mode="Markdown")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("📧 Введите ваш *email*:", parse_mode="Markdown")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("🎂 Введите ваш *возраст*:", parse_mode="Markdown")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("💬 Оставьте *комментарий* (или напишите «нет»):", parse_mode="Markdown")
    return COMMENT

async def get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["comment"] = update.message.text
    context.user_data["username"] = update.message.from_user.username or ""
    context.user_data["user_id"] = update.message.from_user.id

    try:
        save_to_sheet(context.user_data)
        await update.message.reply_text(
            "✅ *Анкета отправлена!* Спасибо за ваши ответы.\n\n"
            "Чтобы пройти заново — /start",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка записи в таблицу: {e}")
        await update.message.reply_text(
            "⚠️ Произошла ошибка при сохранении. Попробуйте позже или свяжитесь с администратором."
        )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Анкета отменена. Напишите /start чтобы начать заново.")
    return ConversationHandler.END

# ─── Запуск ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            AGE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    print("Бот запущен...")
    app.run_polling()
