## -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_TELEGRAM_ID = os.getenv("MANAGER_TELEGRAM_ID")
HELP_URL = os.getenv("HELP_URL")
# DB_HOST = os.getenv("DB_HOST")
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_NAME = os.getenv("DB_NAME")
# DB_TYPE = os.getenv("DB_TYPE", "sqlite") # Выбор СУБД ('mysql' или 'sqlite'). Значение по умолчанию - sqlite
SQLITE_FILE = os.getenv("SQLITE_FILE", "poizon_bot.db")
# # Получение id админов из .env файла, при отсутствии переменной, вернет пустой список
# ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id]


# Создаем каталог для сохранения скриншотов, если его нет
PAY_SCREENS_DIR = "pay_screens"
if not os.path.exists(PAY_SCREENS_DIR):
    os.makedirs(PAY_SCREENS_DIR)

def is_admin(user_id: int) -> bool:
    admin_ids = []
    print(MANAGER_TELEGRAM_ID)
    admin_ids.append(int(MANAGER_TELEGRAM_ID))
    print("admin_ids", admin_ids)
    current_directory = os.path.abspath(".")

    # Выводим его на экран
    print(f"Текущий каталог: {current_directory}")  
    """Проверяет, является ли пользователь администратором."""
    if user_id in admin_ids:
        print('админ')

    return user_id in admin_ids