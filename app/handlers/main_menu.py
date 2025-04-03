from aiogram.fsm.state import State, StatesGroup
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, CallbackQuery
from app.keyboards.user_keyboards import user_inline_menu


router = Router()

@router.callback_query(lambda c: c.data == 'main_menu')
async def process_main_menu(callback_query: types.CallbackQuery):
    """Обрабатывает возврат в главное меню."""
    await send_main_menu(callback_query)




async def send_main_menu(message: types.Message | types.CallbackQuery, text: str = "Основное меню:"):
    """Отправляет главное меню пользователю."""

    if isinstance(message, types.Message):
        await message.answer(text, reply_markup=user_inline_menu)
    elif isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=user_inline_menu)
        await message.answer() #Подтверждаем получение callback_query
