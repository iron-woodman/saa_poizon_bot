from aiogram.filters import CommandStart
from aiogram import types, F, Bot, Router
from pathlib import Path
from aiogram.types import ReplyKeyboardRemove, FSInputFile, CallbackQuery
from app.keyboards.user_keyboards import main_keyboard, user_inline_menu


router = Router()


@router.message(CommandStart())
async def start_command(message: types.Message, bot: Bot):
    """
    Этот обработчик вызывается при команде /start. Отправляет приветственное сообщение и фото.
    """
    image_path = Path("./img/start.jpg")

    if not image_path.exists():
        await message.reply("Ошибка: Файл start.jpg не найден в папке img!")
        return

    try:
        # Используем FSInputFile для указания, что это локальный файл
        photo = FSInputFile(path=str(image_path))

        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo,  # Передаем FSInputFile
            caption=(
                f"""Добро пожаловать!"""
            ),
            reply_markup=main_keyboard
        )
    except Exception as e:
        await message.reply(f"Ошибка при отправке фото: {e}")


@router.message(F.text.regexp(r".*Меню.*"))
async def menu_button_handler(message: types.Message):
    """
    Этот обработчик реагирует на нажатие кнопки, текст которой содержит "Меню", независимо от того, что находится до или после.
    Использует регулярное выражение.
    """
    await message.answer(
        "Основное меню:",
        reply_markup=user_inline_menu
    )


@router.message(F.text == "Помощь")
async def help_handler(message: types.Message) -> None:
    """
    Этот обработчик вызывается при нажатии кнопки "Помощь".
    """
    await message.answer(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "Меню - Открыть меню с действиями\n"
        "Помощь - Получить справку"
    )