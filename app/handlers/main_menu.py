from aiogram.fsm.state import State, StatesGroup
from aiogram import types, F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, CallbackQuery
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from app.keyboards.main_kb import user_inline_menu, otziv_inline_menu
from app.keyboards.calculate_order_kb import registration_keyboard
from app.database.database import Database
from app.config import MANAGER_TELEGRAM_ID


router = Router()


@router.callback_query(lambda c: c.data == 'main_menu' or c.data == 'cancel')
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


@router.callback_query(F.data == 'track_order')
async def track_order(callback_query: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    tg_id = callback_query.from_user.id;
    existing_user = await db.get_user_by_tg_id(tg_id)  # Теперь используем db
    if not existing_user:  #Исправлено: если пользователя нет, то предлагаем зарегистрироваться.
        await callback_query.message.answer(
            "Вы еще не зарегистрированы в системе! Пройдите простую регистрацию.",
            reply_markup=registration_keyboard
        )
        await state.clear() #Сбрасываем состояние
    else:
        try:
            username = callback_query.from_user.username
            user_id = callback_query.from_user.id
            full_name = callback_query.from_user.full_name

            # Формируем сообщение с информацией о пользователе.  Проверяем наличие username.
            if username:
                user_info = f"Пользователь: {full_name} (@{username}, ID: {user_id})"
            else:
                user_info = f"Пользователь: {full_name} (ID: {user_id}, username отсутствует)"

            req_text =f'{user_info} запросил трекинг заказа.'
            await bot.send_message(chat_id=MANAGER_TELEGRAM_ID, text=req_text)
            await callback_query.message.answer("Ваш запрос по трекингу заказа отправлен менеджеру")
        except TelegramForbiddenError:
            print(f"Менеджер с ID {MANAGER_TELEGRAM_ID} заблокировал бота.")
        except TelegramBadRequest as e:
            print(f"Ошибка отправки сообщения менеджеру с ID {MANAGER_TELEGRAM_ID}: {e}")
        except Exception as e:
            print(f"Непредвиденная ошибка при отправке сообщения менеджеру с ID {MANAGER_TELEGRAM_ID}: {e}")

    await callback_query.answer()


@router.callback_query(F.data == 'reviews')
async def track_order(callback_query: CallbackQuery, state: FSMContext):

    await callback_query.message.answer("Нажмите кнопку, чтобы перейти на наш сайт:", 
                                reply_markup=otziv_inline_menu)
    await callback_query.answer()

