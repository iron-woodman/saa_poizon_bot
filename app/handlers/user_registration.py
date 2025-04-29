import logging
from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.config import MANAGER_TELEGRAM_ID
from app.utils.regex import (normolize_phone_number, validate_international_phone_number_basic,
                                  validate_full_name)
from app.keyboards.calculate_order_kb import order_management_keyboard
from app.database.database import Database  # Импортируйте класс Database
from app.database.models import DATABASE_URL  # Импортируйте DATABASE_URL
import asyncio # добавим асинхронность

class UserProfileData(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone_number = State()
    waiting_for_address = State()


logging.basicConfig(level=logging.INFO)

router = Router()

# Создаем экземпляр Database (важно: Singleton гарантирует, что он будет один)
db = Database(DATABASE_URL)  # Инициализация экземпляра Database

@router.callback_query(F.data == "registration")
async def process_confirm_order(callback_query: CallbackQuery, state: FSMContext):
    # Implement order confirmation logic here (e.g., send order details to admin, etc.)
    await callback_query.message.answer("Введите ваше ФИО:")
    await state.clear()  # Clear state after order confirmation
    await state.set_state(UserProfileData.waiting_for_full_name)
    await callback_query.answer()


@router.message(UserProfileData.waiting_for_full_name)
async def register_full_name(message: Message, state: FSMContext):
    full_name = message.text
    if validate_full_name(full_name):
        await state.update_data(full_name=full_name)
        await state.set_state(UserProfileData.waiting_for_phone_number)
        await message.answer('Ваш номер телефона:')
    else:
        await message.answer("Пожалуйста, введите корректные ФИО.")


@router.message(UserProfileData.waiting_for_phone_number)
async def register_phone_number(message: Message, state: FSMContext):
    phone = normolize_phone_number(message.text)
    if validate_international_phone_number_basic(phone):
        await state.update_data(phone_number=phone)
        await state.set_state(UserProfileData.waiting_for_address)
        await message.answer(
            ('Все товары приходят в г. Москва на оптовый рынок "Южные ворота".\n'
             'Вы можете указать именно этот адрес (г. Москва "Южные ворота"), либо любой другой и товар будет отправелен ТК.\n'
        'Укажите адрес доставки:')
        )
    else:
        await message.answer("Пожалуйста, введите корректный номер телефона.")


@router.message(UserProfileData.waiting_for_address)
async def register_user_status(message: Message, state: FSMContext, bot: Bot): # Добавляем bot: Bot в аргументы
    address = message.text
    await state.update_data(address=address)
    data = await state.get_data()
    try:
        data['tg_id'] = message.from_user.id
        data['unique_code'] = 'A001'  # уникальный номер отправления.  Лучше генерировать уникальный код.

        # Добавляем пользователя в базу данных
        user = await db.add_user(
            tg_id=data['tg_id'],
            full_name=data['full_name'],
            phone_number=data['phone_number'],
            main_address=data['address'],
            unique_code=data['unique_code']
        )

        if user:
            logging.info(f"User {user.full_name} (ID: {user.id}) added to the database.")
            success = True
        else:
            logging.warning("Failed to add user to database.  Possibly a duplicate unique_code.")
            success = False #или обрабатываем ошибку

        if success:
            print(f"Заказ пользователя ({data['tg_id']}) успешно добавлен.")
        else:
            print("Failed to add user profile.")


    except Exception as e:
        logging.error(f"Ошибка добавления нового заказа: {e}")
        await state.clear()
        await message.answer("Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
        return #ВАЖНО:  Если произошла ошибка, выходим из функции, чтобы не продолжать отправку сообщений.
    
      # Формируем сообщение для менеджера
    user_info = f"Новый профиль пользователя:\n" \
                f"ФИО: {data.get('full_name', 'Не указано')}\n" \
                f"Телефон: {data.get('phone_number', 'Не указано')}\n" \
                f"Адрес: {data.get('address', 'Не указано')}\n" \
                f"Order_ID: {data.get('unique_code', 'Не указано')}\n" \
                f"Telegram ID: {data.get('tg_id')}\n" \
                f"Telegram Username: @{message.from_user.username if message.from_user.username else 'Не указано'}"
    
     # Отправляем сообщение менеджеру
    try:
        await bot.send_message(chat_id=MANAGER_TELEGRAM_ID, text=user_info)
        logging.info(f"Заказ пользователя {message.from_user.id} отправлены менеджеру {MANAGER_TELEGRAM_ID}")
    except Exception as e:
        logging.error(f"Ошибка при отправке данных менеджеру: {e}")

    await message.answer(
         (
            'Вы успешно зарегистрированы в системе! Ваши контактные данные:'
            f"ФИО: {data.get('full_name', 'Не указано')}\n" \
            f"Телефон: {data.get('phone_number', 'Не указано')}\n" \
            f"Адрес: {data.get('address', 'Не указано')}\n" \
            f"Order_ID: {data.get('unique_code', 'Не указано')}\n" \
            f"Telegram ID: {data.get('tg_id')}\n" \
            f"Telegram Username: @{message.from_user.username if message.from_user.username else 'Не указано'}"
              ),
              reply_markup=order_management_keyboard
              
              )
    await state.clear() #Очищаем стейт после успешной регистрации