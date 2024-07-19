import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('sborka.db')
cursor = conn.cursor()

# Проверка наличия таблицы detail
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detail';")
table_exists = cursor.fetchone()

if table_exists:
    print("Таблица 'detail' существует.")
else:
    print("Таблица 'detail' не существует.")

# Закрытие соединения
conn.close()