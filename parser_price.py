from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import sqlite3
import time
import random
from selenium.webdriver.common.action_chains import ActionChains
import schedule

# Конфигурация
DATABASE = 'sborka.db'
URLS = {
    'Ryzen 5 5600': 'https://www.pleer.ru/product_941639_AMD_Ryzen_5_5600_3500MHzAM4L2L3_35840Kb_100_000000927_OEM.html',
    # Добавьте другие URL-адреса по вашему усмотрению
}

# Убедитесь, что путь к вашему chromedriver указан правильно
CHROME_DRIVER_PATH = 'chromedriver.exe'

def get_price_from_url(url):
    options = Options()
    options.headless = True  # Запуск в фоновом режиме, без открытия окна браузера

    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)
        
        # Прокрутка страницы вниз для загрузки всех элементов
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 5))  # Пауза после прокрутки
        
        # Ожидание до тех пор, пока элемент с классом 'price' не станет доступным
        wait = WebDriverWait(driver, 10)
        price_element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'price'))
        )
        
        if price_element:
            # Получить видимый текст из элемента
            visible_price = price_element.text.strip()
            
            # Найти вложенный элемент с классом 'hide'
            hidden_price_element = price_element.find_element(By.CLASS_NAME, 'hide')
            hidden_price = hidden_price_element.text.strip() if hidden_price_element else None

            # Использовать видимую цену или скрытую цену
            price = hidden_price if hidden_price else visible_price
            
            # Очистить цену от нецифровых символов
            price = ''.join(c for c in price if c.isdigit())
            
            print(f"Найден текст цены: {price}")  # Отладочное сообщение
            return price
        
        print(f"Элемент с классом 'price' не найден на {url}")
    except Exception as e:
        print(f"Ошибка при получении цены с {url}: {e}")
    finally:
        driver.quit()

    return None

def update_prices():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%d.%m.%Y')
    max_history_length = 5  # Максимальное количество записей в истории

    for detail, url in URLS.items():
        print(f"Получение цены для {detail} с {url}...")
        price = get_price_from_url(url)
        if price:
            price_date = f'{price}:{today}'
            # Обновление или добавление новой записи в таблицу
            cursor.execute('''
                SELECT price_data FROM details WHERE detail=?
            ''', (detail,))
            result = cursor.fetchone()
            
            if result:
                # Если запись уже существует, обновить её
                existing_data = result[0]
                data_list = existing_data.split('\n')
                
                # Добавить новую цену
                data_list.append(price_date)
                
                # Оставить только последние max_history_length записей
                if len(data_list) > max_history_length:
                    data_list = data_list[-max_history_length:]
                
                # Обновить запись в базе данных
                new_data = '\n'.join(data_list)
                cursor.execute('''
                    UPDATE details SET price_data=? WHERE detail=?
                ''', (new_data, detail))
                print(f"Запись для {detail} обновлена: {price_date}")  # Отладочное сообщение
            else:
                # Если записи нет, вставить новую
                cursor.execute('''
                    INSERT INTO details (detail, price_data) VALUES (?, ?)
                ''', (detail, price_date))
                print(f"Запись для {detail} добавлена: {price_date}")  # Отладочное сообщение
        
        else:
            print(f"Цена для {detail} не найдена.")  # Отладочное сообщение
        
        # Добавить случайную паузу между запросами
        time.sleep(random.uniform(5, 15))  # Пауза от 5 до 15 секунд
    
    conn.commit()
    conn.close()

# Функция для планирования обновления цен каждые 3 дня
def scheduled_update():
    update_prices()

# Запланируйте выполнение функции каждые 3 дня
schedule.every(3).days.do(scheduled_update)

if __name__ == "__main__":
    print("Запуск планировщика задач. Скрипт будет выполняться каждые 3 дня.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Подождите одну минуту перед следующей проверкой расписания
