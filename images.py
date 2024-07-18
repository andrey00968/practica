import os
import requests

# Список URL-адресов изображений и соответствующие имена файлов
images = {
    "https://c.dns-shop.ru/thumb/st4/fit/300/300/bb717d1e490579d26242eab661b0e432/923c2be60cfd72de7906f3c654d78c880ebec785c7d62041b4bb7713f33acf36.jpg": "processor1.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/98b64b2cc552c05bdb77022ec2f1997c/b14b3e25d62773d234b3cbc4a6d8511774d2594be5ea96871b8821ef46148b8b.jpg": "processor2.jpg",
    "https://c.dns-shop.ru/thumb/st4/fit/300/300/6bd1301600a16b324c82587df1faaf12/406cf857fabcefdf792db46b2faf35f25b57180de76b37f4cd6d31a58501dc18.jpg": "plata1.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/a162cdbf0b7d24f89b12c4f2da146fb5/eeaaf50cde757ab7ce7f5f4135a8660994829a1531384ab4f7e7b4a812926ea8.jpg": "plata2.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/b64d4300b9476a99ae6941d03b5501fa/a1f814393c67b7e16313f5a301ecb203a86be7661b7c3f803a2f0e8389a6e13a.jpg": "ohlad1.jpg",
    "https://c.dns-shop.ru/thumb/st4/fit/300/300/22cbe522c9cd26b52b0969c89a8b1d4d/6b47c90c33c835056c8c7af133960551c418ded60640d4df11f40dd896a611ea.jpg": "ohlad2.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/8f44e72c705f7e84c6e21eefb784c249/10e7c854290ef2a538ce46665325a334b7612a9ebfd3b9c25771fd3021891081.jpg": "memory1.jpg",
    "https://c.dns-shop.ru/thumb/st4/fit/300/300/088dda8e5e47ac2694ef944939d2e0ee/9c4a98b4dd4a5321347f8f84a10ad9ccaa221bd6ecf69d91525f6a993b75fae1.jpg": "memory2.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/b5d8380e6ecec3ba67764f20faa941df/894be0456207386b3ab6051e5b8178c1ba50187fa162afd045e5f05201424497.jpg": "video1.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/ad7b4de1dbad10845ee198f9dbf45336/0a4978d57db3182b8e47aee6c8409ceee6bac27d1d0b3dcf4208f7698c02ba47.jpg": "video2.jpg",
    "https://c.dns-shop.ru/thumb/st4/fit/300/300/6cc919fcdf6c399411ba341f5bd2edde/aa159122f5aea45881c65c6c2b53476f490a8606508be3276158ee3d73c4dfa1.jpg": "blok1.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/771b6cfaebfca421db3dff8ec8d900b6/840d0aa1d080e426c99e02ad19174af61e7c7fda45b7ff3fbf8de26611054313.jpg": "blok2.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/fe1c18feb015e4645ef8e87c42d1671b/a68b90282aad992fb5b47f6a2a8851f6695b8735e9c8bf943b123867f7e4e889.jpg": "nak1.jpg",
    "https://c.dns-shop.ru/thumb/st4/fit/300/300/aa3f32f339adf78ff4a37e80b5b3467b/8525ecb1e107b2579ebc0edb7bf2163b56c43791ffb9e3b04bb1b0e483732b0f.jpg": "nak2.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/09ed23b78e3899807b592a5d17080db1/798fe655026d55c256614413a20cc2f8f27ba7ab977e88397f306811815b5775.jpg": "corp1.jpg",
    "https://c.dns-shop.ru/thumb/st1/fit/300/300/d638f946db37aa7a486c6f16785f070e/36022a812245790b044476e85d851fbf398003c5c7eacb7c76d306d94dd4ea2a.jpg": "corp2.jpg"
}

# Путь к папке static
static_dir = os.path.join(os.getcwd(), 'static')

# Создание папки images внутри папки static, если её не существует
images_dir = os.path.join(static_dir, 'images')
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

# Функция для загрузки изображения
def download_image(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(images_dir, filename), 'wb') as file:
            file.write(response.content)
        print(f"Изображение {filename} успешно загружено.")
    else:
        print(f"Не удалось загрузить изображение {filename} с URL {url}")

# Загрузка всех изображений
for url, filename in images.items():
    download_image(url, filename)