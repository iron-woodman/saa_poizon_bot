import os
from dotenv import load_dotenv

load_dotenv()

print("Загрузка .env...")
print(f"Существует ли файл .env: {os.path.exists('.env')}")  # Проверяем, существует ли файл .env
print(f"Значение BOT_TOKEN из .env: {os.getenv('BOT_TOKEN')}") # Проверяем, читается ли BOT_TOKEN
MANAGER_TELEGRAM_ID = os.getenv("MANAGER_TELEGRAM_ID")
print(f"Значение MANAGER_TELEGRAM_ID из .env: {MANAGER_TELEGRAM_ID}")

if MANAGER_TELEGRAM_ID:
    try:
        MANAGER_TELEGRAM_ID = int(MANAGER_TELEGRAM_ID)
        print(f"MANAGER_TELEGRAM_ID после преобразования в int: {MANAGER_TELEGRAM_ID}")
    except ValueError:
        print("Ошибка: MANAGER_TELEGRAM_ID должен быть целым числом.")
        MANAGER_TELEGRAM_ID = None
else:
    print("Предупреждение: Переменная MANAGER_TELEGRAM_ID не установлена.")
    MANAGER_TELEGRAM_ID = None

def is_admin(user_id: int) -> bool:
    admin_ids = []
    print(f"MANAGER_TELEGRAM_ID в is_admin: {MANAGER_TELEGRAM_ID}") # Проверяем значение внутри функции
    if MANAGER_TELEGRAM_ID is not None:
        admin_ids.append(MANAGER_TELEGRAM_ID)
    print("admin_ids", admin_ids)
    current_directory = os.path.abspath(".")

    # Выводим его на экран
    print(f"Текущий каталог: {current_directory}")
    """Проверяет, является ли пользователь администратором."""
    if user_id in admin_ids:
        print('админ')

    return user_id in admin_ids
