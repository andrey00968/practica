import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# Пример базы данных
DATABASE = "sborka.db"

TARGET_USER_ID = '-4279461578'  # Укажите ID пользователя, которому будут отправляться заявки


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        logging.error(e)
    return conn


def check_username_in_db(username: str) -> bool:
    conn = create_connection(DATABASE)
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM users WHERE user=?", (username,))
        exists = cur.fetchone()[0]
        conn.close()
        return exists > 0
    else:
        logging.error("Ошибка соединения с базой данных")
        return False


def get_user_password_from_db(username: str) -> str:
    conn = create_connection(DATABASE)
    data = 'Нет данных'
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE user=?", (username,))
        row = cur.fetchone()
        if row:
            data = row[0]
        conn.close()
    else:
        logging.error("Ошибка соединения с базой данных")
    return data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['stage'] = 'awaiting_username'
    await update.message.reply_text('Пожалуйста, введите ваше имя пользователя:')


async def check_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('stage') == 'awaiting_username':
        username = update.message.text
        logging.info(f'Проверка имени пользователя: {username}')
        if check_username_in_db(username):
            context.user_data['username'] = username
            context.user_data['stage'] = 'menu'
            logging.info(f"Пользователь найден: {username}")

            keyboard = [
                [
                    InlineKeyboardButton("Написать заявку", callback_data='write_request'),
                    InlineKeyboardButton("Посмотреть данные", callback_data='view_data')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
        else:
            logging.warning(f'Имя пользователя не найдено: {username}')
            await update.message.reply_text('Имя пользователя не найдено. Попробуйте ещё раз или создайте личный кабинет по ссылке:')


async def button_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    username = context.user_data.get('username')
    logging.info(f"Открыто меню для пользователя: {username}")
    if query.data == 'write_request':
        await query.message.reply_text('Введите текст заявки:')
        context.user_data['stage'] = 'writing_request'
    elif query.data == 'view_data':
        user_password = get_user_password_from_db(username)  # Получаем данные пользователя из столбца password
        await query.message.reply_text(f'Конфигурации пользователя {username}: {user_password}')
        context.user_data['stage'] = 'menu'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = context.user_data.get('stage')
    logging.info(f'Текущее действие: {stage}')
    if stage == 'writing_request':
        request_text = update.message.text
        username = context.user_data.get('username')
        logging.info(f'Заявка от {username}: {request_text}')
        await context.bot.send_message(
            chat_id=TARGET_USER_ID,
            text=f'Заявка от {username}: {request_text}'
        )
        await update.message.reply_text('Ваша заявка отправлена.')
        context.user_data['stage'] = 'menu'
    elif stage == 'awaiting_username':
        await check_username(update, context)
    else:
        await update.message.reply_text('Пожалуйста, используйте команды /start, чтобы начать заново.')


def main():
    application = Application.builder().token('7473174060:AAGGGFr80H8aGNAWAEJ17vNULw8OLAzKOII').build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_pressed))

    application.run_polling()


if __name__ == '__main__':
    main()