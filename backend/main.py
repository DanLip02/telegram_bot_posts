from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
import os
load_dotenv()


# Токен, который вы получили от @BotFather
BOT_TOKEN = os.getenv("API_TOKEN")

# Функция-обработчик для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить одежду", callback_data="add_clothes")],
        [InlineKeyboardButton("👔 Подобрать образ", callback_data="create_outfit")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message =f"""
              Привет, {update.effective_user.first_name} !\nПодскажи, что ты хотел бы сделать ? 
              """
    await update.message.reply_text(message, reply_markup=reply_markup)

# Функция-обработчик для команды /add
async def add_clothes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👕 Верх", callback_data="clothes_top")],
        [InlineKeyboardButton("👖 Низ", callback_data="clothes_bottom")],
        [InlineKeyboardButton("👟 Обувь", callback_data="clothes_shoes")],
        [InlineKeyboardButton("🧣 Аксессуары", callback_data="clothes_accessories")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "Какую одежду ты хотел бы добавить?"

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(text=message, reply_markup=reply_markup)
    else:
        # Если это команда /add
        await update.message.reply_text(message, reply_markup=reply_markup)
    # await update.message.reply_text(message)


# Обработчик нажатий на инлайн-кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    data = query.data

    if data == "add_clothes":
        await add_clothes(update, context)
    elif data == "my_wardrobe":
        await query.edit_message_text("Вот твой текущий гардероб...")
    elif data == "create_outfit":
        await query.edit_message_text("Подбираю образ для вас...")
    elif data == "clothes_top":
        await query.edit_message_text("Вы выбрали: Верхняя одежда. Опишите или отправьте фото:")
    elif data == "clothes_bottom":
        await query.edit_message_text("Вы выбрали: Нижняя одежда. Опишите или отправьте фото:")
    elif data == "back_to_main":
        await start_from_callback(update, context)


# Функция для возврата в главное меню из callback
async def start_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить одежду", callback_data="add_clothes")],
        [InlineKeyboardButton("👔 Подобрать образ", callback_data="create_outfit")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = f"""
                  Привет, {update.effective_user.first_name} !\nПодскажи, что ты хотел бы сделать ? 
                  """
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup
    )

# Основная функция
def main():
    # Создаем приложение и передаем ему токен
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Добавляем обработчик для команды /start
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_clothes))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запускаем бота (он будет постоянно опрашивать серверы Telegram)
    application.run_polling()

if __name__ == '__main__':
    main()