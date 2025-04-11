import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Токен твоего бота
TOKEN = '7950888469:AAGWyit3hpBApCJnT8bQQNnYr2qeF5ol_oo'
# Добавь вверху файла рядом с user_data
booked_slots = {}  # Пример: {'2023-04-05': ['10:00', '12:00']}

# Храним записи пользователей в JSON
user_data = {}

# Твой Telegram ID (получить через команду /start)
ADMIN_USER_ID = '1006864922'  # Здесь укажи свой ID

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Кнопки для главного меню
async def start(update: Update, context: CallbackContext) -> None:
    logger.info(f"User {update.message.from_user.id} started interaction.")
    keyboard = [
        [KeyboardButton("Записаться"), KeyboardButton("Мои записи")],
        [KeyboardButton("Профиль"), KeyboardButton("О салоне")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
    await update.message.reply_text('Привет! Чем могу помочь?', reply_markup=reply_markup)

# Обработчик кнопки "Записаться"
async def book_massage(update: Update, context: CallbackContext) -> None:
    logger.info(f"User {update.message.from_user.id} selected 'Записаться'.")
    keyboard = [
        [KeyboardButton("Массаж спины"), KeyboardButton("Массаж спины+руки+ШВЗ")],
        [KeyboardButton("Массаж ШВЗ"), KeyboardButton("Общий классический массаж")],
        [KeyboardButton("Назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
    await update.message.reply_text('Выберите массаж:', reply_markup=reply_markup)

# Обработчик записи массажа
async def handle_massage(update: Update, context: CallbackContext) -> None:
    massage = update.message.text
    user_id = update.message.from_user.id
    user_data.setdefault(user_id, {}).update({'massage': massage})

    logger.info(f"User {user_id} selected massage: {massage}")

    # Предлагаем выбрать дату
    keyboard = [
        [KeyboardButton("2023-04-05"), KeyboardButton("2023-04-06"), KeyboardButton("2023-04-07")],
        [KeyboardButton("Назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
    await update.message.reply_text(f'Вы выбрали: {massage}. Теперь выберите дату:', reply_markup=reply_markup)

# Обработчик выбора даты
async def handle_date(update: Update, context: CallbackContext) -> None:
    date = update.message.text
    user_id = update.message.from_user.id
    user_data[user_id].update({'date': date})

    logger.info(f"User {user_id} selected date: {date}")

    # Предлагаем выбрать время
    keyboard = [
        [KeyboardButton("10:00"), KeyboardButton("12:00"), KeyboardButton("14:00")],
        [KeyboardButton("16:00"), KeyboardButton("18:00")],
        [KeyboardButton("Назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
    await update.message.reply_text(f'Вы выбрали: {date}. Теперь выберите время:', reply_markup=reply_markup)

# Обработчик времени
async def handle_time(update: Update, context: CallbackContext) -> None:
    time = update.message.text
    user_id = update.message.from_user.id
    user_data[user_id].update({'time': time})

    logger.info(f"User {user_id} selected time: {time}")

    # Сохраняем запись
    massage = user_data[user_id]['massage']
    date = user_data[user_id]['date']
    time = user_data[user_id]['time']
    await update.message.reply_text(f'Запись на массаж: {massage} {date} в {time}.!')

    # Добавляем запись в список
    user_data[user_id].setdefault('bookings', []).append({'massage': massage, 'date': date, 'time': time})

    # Отправляем уведомление в ЛС администратору
    bot = context.bot
    await bot.send_message(ADMIN_USER_ID, f'Новая запись:\n{massage} - {date} в {time}')

    # Главное меню
    await start(update, context)

# Обработчик команды "Мои записи"
async def my_bookings(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_data or 'bookings' not in user_data[user_id]:
        await update.message.reply_text('У вас нет записей.')
    else:
        bookings = user_data[user_id]['bookings']
        message = "\n".join([f'{b["massage"]} - {b["date"]} в {b["time"]}' for b in bookings])
        await update.message.reply_text(f'Ваши записи:\n{message}')
    await start(update, context)

# Обработчик команды "Профиль"
async def profile(update: Update, context: CallbackContext) -> None:
    user_info = update.message.from_user
    await update.message.reply_text(f'Ваш профиль:\nИмя: {user_info.first_name}\nID: {user_info.id}')
    
    # Кнопка назад
    keyboard = [
        [KeyboardButton("Назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text('Нажмите "Назад", чтобы вернуться в меню.', reply_markup=reply_markup)

# Основная функция
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("my_bookings", my_bookings))
    application.add_handler(MessageHandler(filters.Regex('^Записаться$'), book_massage))
    application.add_handler(MessageHandler(filters.Regex('^Мои записи$'), my_bookings))
    application.add_handler(MessageHandler(filters.Regex('^Профиль$'), profile))
    application.add_handler(MessageHandler(filters.Regex('^Назад$'), start))

    # Обработчики выбора массажа, даты и времени
    application.add_handler(MessageHandler(filters.Regex('^(Массаж спины|Массаж спины\+руки\+ШВЗ|Массаж ШВЗ|Общий классический массаж)$'), handle_massage))
    application.add_handler(MessageHandler(filters.Regex('^(2023-04-05|2023-04-06|2023-04-07)$'), handle_date))
    application.add_handler(MessageHandler(filters.Regex('^(10:00|12:00|14:00|16:00|18:00)$'), handle_time))

    application.run_polling()

if __name__ == '__main__':
    main()
