import schedule
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import sqlite3
import random

# Конфигурация
DATABASE = 'sborka.db'
URLS = {
    'Ryzen 5 5600': 'https://www.pleer.ru/product_941639_AMD_Ryzen_5_5600_3500MHzAM4L2L3_35840Kb_100_000000927_OEM.html',
    'Ryzen 7 5800X': 'https://www.pleer.ru/product_806619_AMD_Ryzen_7_5800X_100_000000063_OEM.html',
    'MSI A520M-A PRO': 'https://www.pleer.ru/product_987306_MSI_A520M_A_Pro.html',
    'MSI B550-A PRO': 'https://www.pleer.ru/product_775518_MSI_B550_A_Pro.html',
    'DEEPCOOL AG200': 'https://www.pleer.ru/product_992860_DeepCool_AG200_R_AG200_BKNNMN_G_Intel_LGA17001200115111501155_AMD_AM5AM4.html',
    'ID-COOLING SE-224-XTS': 'https://www.pleer.ru/product_983321_ID_Cooling_SE_224_XTS_Black_Intel_LGA115011511151_v21155115612001700_AMD_AM5AM4.html',
    'ADATA XPG GAMMIX D10 16 GB': 'https://www.pleer.ru/product_959599_A_Data_XPG_Gammix_D10_DDR4_DIMM_3200MHz_PC25600_CL16_8Gb_AX4U32008G16A_SB10.html',
    'Kingston FURY Beast Black 32 GB': 'https://www.pleer.ru/product_863483_Kingston_Fury_Beast_Black_DDR4_DIMM_3600Mhz_PC28800_CL18_32Gb_Kit_2x16Gb_KF436C18BBK232.html', 
    'Palit GeForce RTX 3050 StormX': 'https://www.pleer.ru/product_1034905_Palit_nVidia_GeForce_RTX_3050_StormX_OC_1042Mhz_PCI_E_40_6144Mb_14000Mhz_96_bit_DP_HDMI_DVI_NE63050S18JE_1070F.html',
    'KFA2 GeForce RTX 4070 X 3FAN Black': 'https://www.pleer.ru/product_1000386_ASUS_GeForce_RTX_4070_TUF_Gaming_12G_OC_2550Mhz_PCI_E_40_12288Mb_22000Mhz_192_bit_HDMI_3xDP_TUF_RTX4070_O12G_GAMING.html',
    'DEEPCOOL PF450': 'https://www.pleer.ru/product_992853_DeepCool_PF450_450W_80_Plus_R_PF450D_HA0B_EU.html',
    'be quiet! Pure Power 11 600W': 'https://www.pleer.ru/product_617197_Be_Quiet_Pure_Power_11_600W.html',
    'ADATA LEGEND 700 GOLD 512 GB': 'https://www.pleer.ru/product_1033234_A_Data_Legend_700_512Gb_SLEG_700G_512GCS_SH7.html',
    'Samsung 980 1000 GB': 'https://www.pleer.ru/product_827125_Samsung_980_1Tb_MZ_V8V1T0BW.html',
    'DEEPCOOL MATREXX 30': 'https://www.pleer.ru/product_660187_DeepCool_Matrexx_30_mATX_Black_bez_BP.html',
    'DEEPCOOL MATREXX 50': 'https://www.pleer.ru/product_660372_DeepCool_Matrexx_50_Black_bez_BP.html'
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
            price_date = f'{price}:{today}'.strip()  # Формируем запись цены и даты
            
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
                new_data = '\n'.join(data_list).strip()
                cursor.execute('''
                    UPDATE details SET price_data=? WHERE detail=?
                ''', (new_data, detail))
                print(f"Запись для {detail} обновлена: {price_date}")
            else:
                # Если записи нет, вставить новую
                cursor.execute('''
                    INSERT INTO details (detail, price_data) VALUES (?, ?)
                ''', (detail, price_date))
                print(f"Запись для {detail} добавлена: {price_date}")
        
        else:
            print(f"Цена для {detail} не найдена.")
        
        # Добавить случайную паузу между запросами
        time.sleep(random.uniform(5, 15))
    
    conn.commit()
    conn.close()


def job():
    print(f"Запуск обновления цен: {datetime.now()}")
    update_prices()

# Планирование выполнения каждые 2 дня
schedule.every(2).days.do(job)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(30)