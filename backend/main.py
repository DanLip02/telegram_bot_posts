from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
import os
from database import db
load_dotenv()

# Временное хранилище для состояний пользователей
user_states = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    user_db = db.get_or_create_user_simple(user)

    if user_db:
        welcome_text = f"Рад снова тебя видеть, {user.first_name}! 😊"
    else:
        welcome_text = f"Привет, {user.first_name}! Добро пожаловать! 🎉"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить одежду", callback_data="add_clothes")],
        [InlineKeyboardButton("👔 Подобрать образ", callback_data="create_outfit")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = f"{welcome_text}\nПодскажи, что ты хотел бы сделать?"

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


async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, category):
    """Обработчик выбора категории"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Сохраняем состояние пользователя
    user_states[user.id] = {
        'category': category,
        'step': 'waiting_description'
    }

    category_names = {
        "clothes_top": "👕 Верхняя одежда",
        "clothes_bottom": "👖 Нижняя одежда",
        "clothes_shoes": "👟 Обувь",
        "clothes_accessories": "🧣 Аксессуары"
    }

    category_name = category_names.get(category, "Одежда")

    await query.edit_message_text(
        f"Вы выбрали: {category_name}\n\n"
        "Теперь опишите эту вещь:\n"
        "• Название/тип\n"
        "• Цвет\n"
        "• Размер\n"
        "• Состояние\n"
        "• Особенности\n\n"
        "Пример: *Красная футболка Nike, размер M, отличное состояние*",
        parse_mode='Markdown'
    )

async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстового описания"""
    user = update.effective_user
    description = update.message.text

    if user.id in user_states and user_states[user.id]['step'] == 'waiting_description':
        # Сохраняем описание
        user_states[user.id]['description'] = description
        user_states[user.id]['step'] = 'waiting_photo'

        await update.message.reply_text(
            "📝 Отлично! Описание сохранено.\n\n"
            "Теперь отправьте фото этой вещи:"
        )
    else:
        await update.message.reply_text("❌ Сначала выберите категорию через /start")



async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фото"""
    user = update.effective_user

    if user.id in user_states and user_states[user.id]['step'] == 'waiting_photo':
        # Получаем фото
        photo = update.message.photo[-1]
        file_id = photo.file_id

        user_data = user_states[user.id]

        # Сохраняем в БД
        post = db.add_product_simple(
            user=user,
            category=user_data['category'],
            description=user_data['description'],
            photo_file_id=file_id
        )

        if post:
            # Очищаем состояние
            del user_states[user.id]

            await update.message.reply_text(
                "✅ Отлично! Публикация сохранена!\n\n"
                f"🆔 ID публикации: #{post['id']}\n"
                f"📂 Категория: {user_data['category']}\n"
                f"📝 Описание: {user_data['description']}\n\n"
                "Что дальше?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Добавить еще", callback_data="add_clothes")],
                    [InlineKeyboardButton("📋 Мои публикации", callback_data="my_posts")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
                ])
            )
        else:
            await update.message.reply_text("❌ Ошибка при сохранении в базу данных")
    else:
        await update.message.reply_text("❌ Сначала опишите вещь")

async def show_user_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать публикации пользователя"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    posts = db.get_user_posts(user.id)

    if not posts:
        await query.edit_message_text(
            "📋 У вас пока нет публикаций.\n\n"
            "Добавьте первую вещь в свой гардероб!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить одежду", callback_data="add_clothes")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
            ])
        )
        return

    message = "📋 Ваши публикации:\n\n"
    for post in posts[:10]:  # Показываем первые 10
        message += f"• #{post['id']} - {post['category']}\n"
        message += f"  {post['description'][:50]}...\n\n"

    if len(posts) > 10:
        message += f"... и еще {len(posts) - 10} публикаций"

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить еще", callback_data="add_clothes")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
        ])
    )

# Обработчик нажатий на инлайн-кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "add_clothes":
        await add_clothes(update, context)
    elif data == "my_posts":
        await show_user_posts(update, context)
    elif data == "create_outfit":
        await query.edit_message_text("Подбираю образ для вас...")
    elif data in ["clothes_top", "clothes_bottom", "clothes_shoes", "clothes_accessories"]:
        await handle_category_selection(update, context, data)
    elif data == "back_to_main":
        await start_from_callback(update, context)
    elif data == "help":
        await query.edit_message_text(
            "🤖 Помощь по боту:\n\n"
            "• Добавить одежду - загрузите вещи в свой гардероб\n"
            "• Мои публикации - просмотр всех ваших вещей\n"
            "• Подобрать образ - создайте комплект из вашей одежды"
        )


# Функция для возврата в главное меню из callback
async def start_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить одежду", callback_data="add_clothes")],
        [InlineKeyboardButton("📋 Мои публикации", callback_data="my_posts")],
        [InlineKeyboardButton("👔 Подобрать образ", callback_data="create_outfit")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = f"Привет, {update.effective_user.first_name}!\nПодскажи, что ты хотел бы сделать?"

    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup
    )

def main():
    # Токен, который вы получили от @BotFather

    BOT_TOKEN = os.getenv("API_TOKEN")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🚀 Бот запущен с подключением к БД!")
    application.run_polling()

if __name__ == '__main__':
    main()