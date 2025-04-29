import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.handlers import start, main_menu, order_type, user_registration, compile_order, help, admin
from app.database import database
from app.config import BOT_TOKEN
from app.database.database import Database  # Импортируйте класс Database
from app.database.models import DATABASE_URL  # Импортируйте DATABASE_URL
from app.middlewares.database import DatabaseMiddleware

async def main():
    if not BOT_TOKEN:
        exit("Error: No telegram bot token provided")

    db = Database(DATABASE_URL)  # Создаем экземпляр Database

    # Создаем экземпляр Bot с использованием DefaultBotProperties
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    await db.create_db_and_tables() #Убедитесь, что таблицы созданы
    # Зарегистрируйте Middleware
    dp.message.middleware(DatabaseMiddleware(db))
    dp.callback_query.middleware(DatabaseMiddleware(db))

    # Подключаем роутеры (обработчики)
    dp.include_router(start.router)
    dp.include_router(order_type.router)
    dp.include_router(main_menu.router)
    dp.include_router(user_registration.router)
    dp.include_router(compile_order.router)
    dp.include_router(help.router)
    dp.include_router(admin.router)
 


    # Запускаем бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен.')
    except Exception as e:
        logging.error(f"Произошла ошибка при запуске бота: {e}")
