import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
from app.handlers import start, main_menu, calculate_price, order_type
from app.database import database
from aiogram.enums import ParseMode

async def main():
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        exit("Error: No token provided")

    # Создаем экземпляр Bot с использованием DefaultBotProperties
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Подключаем роутеры (обработчики)
    dp.include_router(start.router)
    dp.include_router(order_type.router)
    dp.include_router(main_menu.router)


    # Инициализация базы данных
    # database.create_db()


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
