import logging
import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Параметры базы данных
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'sborka.db')
TARGET_USER_ID = '-4279461578'
user_to_target_message_map = {}

# Функция создания соединения с базой данных
def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        logging.error(e)
    return conn

# Функция проверки наличия пользователя в базе данных
def check_username_in_db(username: str) -> bool:
    conn = create_connection(DATABASE)
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM users WHERE username=?", (username,))
        exists = cur.fetchone()[0]
        conn.close()
        return exists > 0
    else:
        logging.error("Ошибка соединения с базой данных")
        return False

# Функция получения пароля пользователя из базы данных
def get_user_password_from_db(username: str) -> str:
    conn = create_connection(DATABASE)
    data = 'Нет данных'
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if row:
            data = str(row[0])
        conn.close()
    else:
        logging.error("Ошибка соединения с базой данных")
    return data

# Функция обновления заявок пользователя в базе данных
def update_user_request_in_db(username: str, request_text: str) -> None:
    conn = create_connection(DATABASE)
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT zayavki FROM users WHERE username=?", (username,))
        result = cur.fetchone()
        current_requests = result[0] if result else ''
        next_request_number = current_requests.count('№') + 1 if current_requests else 1
        new_request = f'№{next_request_number}: "{request_text}"\n'
        updated_requests = current_requests + new_request if current_requests else new_request
        cur.execute("UPDATE users SET zayavki=? WHERE username=?", (updated_requests, username))
        conn.commit()
        conn.close()
    else:
        logging.error("Ошибка соединения с базой данных")

# Асинхронная функция начала работы бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['stage'] = 'awaiting_username'
    await update.message.reply_text('Пожалуйста, введите ваше имя пользователя:')

# Асинхронная функция проверки имени пользователя
async def check_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('stage') == 'awaiting_username':
        username = update.message.text
        logging.info(f'Проверка имени пользователя: {username}')
        if check_username_in_db(username):
            context.user_data['username'] = username
            context.user_data['stage'] = 'awaiting_password'
            await update.message.reply_text('Пожалуйста, введите ваш пароль:')
        else:
            logging.warning(f'Имя пользователя не найдено: {username}')
            await update.message.reply_text('Имя пользователя не найдено. Попробуйте ещё раз или создайте личный кабинет по ссылке:')

# Асинхронная функция проверки пароля пользователя
async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('stage') == 'awaiting_password':
        password = update.message.text.strip()
        username = context.user_data.get('username')
        correct_password = get_user_password_from_db(username).strip()
        logging.info(f'Полученный пароль: "{password}"')
        logging.info(f'Ожидаемый пароль: "{correct_password}"')
        if password == correct_password:
            context.user_data['stage'] = 'menu'
            logging.info(f"Пароль подтвержден для пользователя: {username}")

            keyboard = [
                [
                    InlineKeyboardButton("Написать заявку", callback_data='write_request'),
                    InlineKeyboardButton("Посмотреть данные", callback_data='view_data')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
        else:
            logging.warning(f'Неверный пароль для пользователя: {username}')
            await update.message.reply_text('Неверный пароль. Попробуйте ещё раз:')

# Асинхронная функция обработки нажатия кнопок
async def button_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    username = context.user_data.get('username')
    logging.info(f"Открыто меню для пользователя: {username}")
    if query.data == 'write_request':
        await query.message.reply_text('Введите текст заявки:')
        context.user_data['stage'] = 'writing_request'
    elif query.data == 'view_data':
        keyboard = [
            [
                InlineKeyboardButton("Мои заявки", callback_data='my_requests'),
                InlineKeyboardButton("Мои конфигурации", callback_data='my_configurations')
            ],
            [InlineKeyboardButton("Назад", callback_data='go_back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('Выберите опцию:', reply_markup=reply_markup)
    elif query.data == 'my_requests':
        requests_data = get_requests_data_from_db(username)
        await query.message.reply_text(f'Ваши заявки:\n{requests_data}')
    elif query.data == 'my_configurations':
        configurations_data = get_sborki_data_from_db(username)
        await query.message.reply_text(f'Ваши конфигурации:\n\n{configurations_data} \n\n\n1 - конфигурация принята, 2 - конфигурация выполнена, 3 - конфигурация отклонена')
    elif query.data == 'go_back':
        keyboard = [
            [
                InlineKeyboardButton("Написать заявку", callback_data='write_request'),
                InlineKeyboardButton("Посмотреть данные", callback_data='view_data')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('Выберите действие:', reply_markup=reply_markup)

def get_requests_data_from_db(username: str) -> str:
    conn = create_connection(DATABASE)
    data = 'Нет данных'
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT zayavki FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if row:
            data = str(row[0])
            data += '\n1 - заявка принята, 2 - заявка выполнена, 3 - заявка отклонена'
        conn.close()
    else:
        logging.error("Ошибка соединения с базой данных")
    return data

# Функция получения данных сборки пользователя из базы данных
def get_sborki_data_from_db(username: str) -> str:
    conn = create_connection(DATABASE)
    data = 'Нет данных'
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT sborki FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if row:
            data = str(row[0])
        conn.close()
    else:
        logging.error("Ошибка соединения с базой данных")
    return data

# Асинхронная функция обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = context.user_data.get('stage')
    logging.info(f'Текущее действие: {stage}')
    
    if stage == 'writing_request':
        request_text = update.message.text
        username = context.user_data.get('username')
        logging.info(f'Заявка от {username}: {request_text}')

        # Проверка на наличие абзацев
        if '\n' in request_text:
            await update.message.reply_text('Заявка не может быть отправлена, так как в ней используются абзацы. Пожалуйста, отправьте заявку заново без абзацев.')
        else:
            # Проверка длины слов
            words = request_text.split()
            too_long_words = [word for word in words if len(word) > 20]
            
            if too_long_words:
                long_words_list = ', '.join(too_long_words)
                await update.message.reply_text(f'Вы используете слишком длинные слова: {long_words_list}. Попробуйте отправить заявку ещё раз.')
            else:
                # Обновление заявок в базе данных
                update_user_request_in_db(username, request_text)
                await context.bot.send_message(
                    chat_id=TARGET_USER_ID,
                    text=f'Заявка от {username}: {request_text}'
                )
                await update.message.reply_text('Ваша заявка отправлена.')
                context.user_data['stage'] = 'menu'
    
    elif stage == 'awaiting_username':
        await check_username(update, context)
    
    elif stage == 'awaiting_password':
        await check_password(update, context)
    
    else:
        await update.message.reply_text('Пожалуйста, используйте команды /start, чтобы начать заново.')

# Основная функция запуска бота
def main():
    application = Application.builder().token('7473174060:AAGGGFr80H8aGNAWAEJ17vNULw8OLAzKOII').build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_pressed))

    application.run_polling()

if __name__ == '__main__':
    main()