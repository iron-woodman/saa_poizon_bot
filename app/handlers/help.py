from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types, Router, Bot, F
from aiogram.types import User
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from app.config import MANAGER_TELEGRAM_ID


# Создаем роутер
router = Router()

class Form(StatesGroup):
    waiting_for_question = State() # Состояние ожидания вопроса


async def send_message_to_manager(bot: Bot, manager_id: int, user: User, text: str) -> bool:
    """
    Отправляет сообщение менеджеру по его Telegram ID, включая ID и имя пользователя.

    Args:
        bot: Объект бота aiogram.
        manager_id: ID телеграм менеджера.
        user: Объект User, представляющий пользователя, отправившего сообщение.
        text: Текст сообщения.

    Returns:
        True, если сообщение отправлено успешно, False в противном случае.
    """
    username = user.username
    user_id = user.id
    full_name = user.full_name

    # Формируем сообщение с информацией о пользователе.  Проверяем наличие username.
    if username:
        user_info = f"Пользователь: {full_name} (@{username}, ID: {user_id})"
    else:
        user_info = f"Пользователь: {full_name} (ID: {user_id}, username отсутствует)"


    message_text = f"{user_info}\n\n{text}"  # Объединяем информацию и текст сообщения

    try:
        await bot.send_message(chat_id=manager_id, text=message_text)
        return True
    except TelegramForbiddenError:
        print(f"Менеджер с ID {manager_id} заблокировал бота.")
        return False
    except TelegramBadRequest as e:
        print(f"Ошибка отправки сообщения менеджеру с ID {manager_id}: {e}")
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка при отправке сообщения менеджеру с ID {manager_id}: {e}")
        return False


@router.callback_query(F.data == 'request_help')
async def handle_support_callback(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 
                           "Пожалуйста, напишите ваш вопрос. Он будет отправлен менеджеру поддержки.")
    await state.set_state(Form.waiting_for_question) # Устанавливаем состояние ожидания вопроса
    # await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id) # Optional
    

@router.message(Form.waiting_for_question)
async def process_user_question(message: types.Message, state: FSMContext, bot: Bot):
    question = message.text
    success = await send_message_to_manager(bot, MANAGER_TELEGRAM_ID, message.from_user,
                                            f"Вопрос от пользователя: {question}")
    if success:
        await message.reply("Ваш вопрос отправлен менеджеру поддержки. Ожидайте ответа.")
    else:
        await message.reply("Не удалось отправить вопрос менеджеру поддержки. Попробуйте позже.")
    await state.clear()  # Сбрасываем состояние

