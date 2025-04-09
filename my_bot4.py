import json
import random
from datetime import timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

RATING_FILE = "rating.json"
users_last_choice_time = {}

def load_rating(chat_id):
    try:
        with open(RATING_FILE, "r") as f:
            ratings = json.load(f)
            return ratings.get(str(chat_id), {})
    except:
        return {}

def save_rating(chat_id, rating):
    try:
        with open(RATING_FILE, "r") as f:
            ratings = json.load(f)
    except:
        ratings = {}

    ratings[str(chat_id)] = rating

    with open(RATING_FILE, "w") as f:
        json.dump(ratings, f)

async def get_all_members(chat_id, context: ContextTypes.DEFAULT_TYPE):
    members = []
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        for admin in admins:
            members.append(admin.user)
    except Exception as e:
        print(f"Ошибка при получении администраторов чата: {e}")
    return members

async def send_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        keyboard = [
            [InlineKeyboardButton("Старт", callback_data="start_choice")],
            [InlineKeyboardButton("Рейтинг", callback_data="view_rating")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def start_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.callback_query.message
    current_time = message.date.timestamp()

    if chat_id in users_last_choice_time:
        elapsed = current_time - users_last_choice_time[chat_id]
        if elapsed < 43200:
            remaining = 43200 - elapsed
            remaining_time = str(timedelta(seconds=int(remaining)))
            await message.edit_text(f"❗ Выбор можно сделать не чаще, чем раз в 12 часов.\nОсталось: {remaining_time}")
            return

    users = await get_all_members(chat_id, context)
    users = [user for user in users if not user.is_bot]

    if users:
        rating = load_rating(chat_id)

        for user in users:
            user_id = str(user.id)
            if user_id not in rating:
                rating[user_id] = 0

        selected = random.choice(users)
        selected_id = str(selected.id)
        rating[selected_id] += 1
        save_rating(chat_id, rating)
        users_last_choice_time[chat_id] = current_time

        name = f"@{selected.username}" if selected.username else selected.full_name
        await message.edit_text(f"🎉 Пидор дня: {name}")
    else:
        await message.edit_text("❗ В группе нет участников для выбора.")

async def view_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.callback_query.message
    rating = load_rating(chat_id)

    if not rating:
        await message.edit_text("📊 Рейтинг пока пуст.")
        return

    sorted_rating = sorted(rating.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 Текущий рейтинг:\n"
    for user_id, count in sorted_rating:
        try:
            user = await context.bot.get_chat_member(chat_id, int(user_id))
            username = f"@{user.user.username}" if user.user.username else user.user.full_name
            text += f"{username}: {count} раз(а)\n"
        except Exception as e:
            text += f"User {user_id}: {count} раз(а)\n"

    await message.edit_text(text)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_choice":
        await start_choice(update, context)
    elif query.data == "view_rating":
        await view_rating(update, context)

def main():
    application = Application.builder().token("7730168646:AAHPj6NRIHzYrZ6JNUG2O_VMjMsZMoU6Mbo").build()

    application.add_handler(CommandHandler("start", send_buttons))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
