from aiogram.filters import CommandStart
from aiogram import types, F, Bot, Router
from pathlib import Path
from aiogram.types import ReplyKeyboardRemove, FSInputFile, CallbackQuery
from app.keyboards.main_kb import main_keyboard, user_inline_menu
from app.keyboards.admin_kb import admin_keyboard
from app.config import is_admin


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
        photo = FSInputFile(path=str(image_path))
        print("message.from_user.id=", message.from_user.id)
        if is_admin(message.from_user.id):
            # Пользователь - администратор, отправляем админ-меню
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption="Добро пожаловать, администратор!",
                reply_markup=admin_keyboard # Отправляем клавиатуру администратора
            )

        else:
            # Обычный пользователь, отправляем обычное меню
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption="Добро пожаловать!",
                reply_markup=main_keyboard  # Отправляем основную клавиатуру
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


@router.message(F.text.regexp(r".*Помощь.*"))
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