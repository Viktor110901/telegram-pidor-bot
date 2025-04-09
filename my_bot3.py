import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

RATING_FILE = "rating.json"
users_last_choice_time = {}

# Функция для загрузки рейтинга для конкретного чата
def load_rating(chat_id):
    try:
        with open(RATING_FILE, "r") as f:
            ratings = json.load(f)
            return ratings.get(str(chat_id), {})  # Возвращаем рейтинг для конкретного чата
    except:
        return {}

# Функция для сохранения рейтинга для конкретного чата
def save_rating(chat_id, rating):
    try:
        with open(RATING_FILE, "r") as f:
            ratings = json.load(f)
    except:
        ratings = {}

    ratings[str(chat_id)] = rating  # Сохраняем рейтинг для конкретного чата

    with open(RATING_FILE, "w") as f:
        json.dump(ratings, f)

# Функция для получения администраторов чата
async def get_all_members(chat_id, context: ContextTypes.DEFAULT_TYPE):
    members = []
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        for admin in admins:
            members.append(admin.user)  # Добавляем каждого администратора в список
    except Exception as e:
        print(f"Ошибка при получении администраторов чата: {e}")
    return members

# Функция для отправки кнопок "Старт" и "Рейтинг"
async def send_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        keyboard = [
            [InlineKeyboardButton("Старт", callback_data="start_choice")],
            [InlineKeyboardButton("Рейтинг", callback_data="view_rating")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Функция для выбора случайного пользователя
async def start_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_time = update.callback_query.message.date.timestamp()

    # Проверяем, если прошло меньше 12 часов с последнего выбора
    if chat_id in users_last_choice_time and current_time - users_last_choice_time[chat_id] < 43200:
        await update.callback_query.message.reply_text("Выбор можно сделать не чаще, чем раз в 12 часов.")
        return

    # Получаем всех участников чата (администраторов)
    users = await get_all_members(chat_id, context)

    # Исключаем бота из списка участников
    users = [user for user in users if not user.is_bot]

    if users:
        # Загружаем текущий рейтинг для конкретного чата
        rating = load_rating(chat_id)

        # Добавляем всех пользователей в рейтинг, если их нет
        for user in users:
            user_id = str(user.id)
            if user_id not in rating:
                rating[user_id] = 0  # Начальный счёт 0

        # Выбираем случайного пользователя
        selected = random.choice(users)

        # Обновляем рейтинг
        user_id = str(selected.id)
        rating[user_id] += 1  # Увеличиваем счёт выбранного

        # Сохраняем обновлённый рейтинг
        save_rating(chat_id, rating)

        # Обновляем время последнего выбора
        users_last_choice_time[chat_id] = current_time

        # Отправляем сообщение о выбранном пользователе
        await update.callback_query.message.reply_text(f"🎉 Пидор дня: {selected.full_name}")
    else:
        await update.callback_query.message.reply_text("В группе нет участников для выбора.")

# Функция для отображения рейтинга
async def view_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rating = load_rating(chat_id)

    if not rating:
        await update.callback_query.message.reply_text("Рейтинг пока пуст.")
        return

    # Сортируем рейтинг по убыванию количества выборов
    sorted_rating = sorted(rating.items(), key=lambda x: x[1], reverse=True)

    # Формируем сообщение с рейтингом
    text = "🏆 Текущий рейтинг:\n"
    for user_id, count in sorted_rating:
        try:
            user = await context.bot.get_chat_member(chat_id, int(user_id))
            text += f"{user.user.full_name}: {count} раз(а)\n"
        except Exception as e:
            text += f"User {user_id}: {count} раз(а)\n"

    await update.callback_query.message.reply_text(text)

# Обработчик для нажатия на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_choice":
        await start_choice(update, context)
    elif query.data == "view_rating":
        await view_rating(update, context)

# Главная функция
def main():
    application = Application.builder().token("7730168646:AAHPj6NRIHzYrZ6JNUG2O_VMjMsZMoU6Mbo").build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", send_buttons))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
