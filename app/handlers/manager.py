import os
import json
import logging
from typing import Dict, Any
from aiogram import F, Router, Bot
from aiogram.types import (Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, Document,
    InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, List

from app.database.database import Database
from app.database.models import Order
from app.keyboards.manager_kb import (create_inline_keyboard, CALLBACK_DATA_PREFIX, 
                                    order_status_keyboard, manager_keyboard)

# Получите логгер
logger = logging.getLogger(__name__)

router = Router()

# FSM для запроса user_code
class ManagerStates(StatesGroup):
    waiting_for_order_code= State()
    waiting_for_user_code= State()


# Вспомогательная функция для форматирования данных заказа в строку
def format_order_data(order: Order) -> str:
    """Форматирует данные заказа в строку для телеграм-поста."""
    user = order.user  # Получаем связанного пользователя
    if user:
        return (
            f"Код заказа: {order.id}\n"
            f"Код пользователя: {user.unique_code}\n"
            # f"Телеграм: {user.telegram_link}\n"
            f"Адрес доставки: {user.main_address}\n"
            f"---\n"
        )
    else:
        return f"Ошибка: Не удалось получить данные пользователя для заказа {order.order_code}\n---\n"
    

def format_order_for_telegram(order: Order) -> str:
    """
    Форматирует информацию о заказе для отправки в Telegram-боте.
    Добавляет эмодзи для улучшения восприятия.
    """
    message = f"📦 *Заказ №{order.id}*\n\n"  # Используем order_code вместо order.id
    message += f"🗓️ Дата заказа: {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"  # Более читаемый формат даты
    message += f"🏷️ Категория: {order.category}\n"
    message += f"📏 Размер: {order.size}\n"
    message += f"🎨 Цвет: {order.color}\n"
    message += f"🔗 Ссылка: {order.link}\n"
    message += f"💰 Цена товара: {order.price:.2f}\n"
    message += f"🚚 Способ доставки: {order.delivery_method}\n"
    message += f"💲 Общая цена (с доставкой): {order.total_price:.2f}\n"

    if order.promocode:
        message += f"🎫 Промокод: {order.promocode}\n"

    message += f"🚦 Статус: {order.status}\n"

    if order.tracking_number:
        message += f"🔎 Номер отслеживания: {order.tracking_number}\n"
    if order.estimated_delivery:
        message += f"🚚 Ожидаемая дата доставки: {order.estimated_delivery.strftime('%d.%m.%Y')}\n"  # Формат даты

    # Дополнительная информация в зависимости от статуса
    # if order.status == "Оплачен":
    #     message += "✅ Заказ оплачен, ожидаем подтверждения.\n"
    # elif order.status == "В обработке":
    #     message += "🛠️ Заказ в обработке.\n"
    # elif order.status == "Отправлен":
    #     message += "🚀 Заказ отправлен!\n"
    # elif order.status == "Завершен":
    #     message += "🎉 Заказ завершен. Спасибо за покупку!\n"
    # elif order.status == "Отменен":
    #     message += "❌ Заказ отменен.\n"
    # elif order.status == "Создан":
    #     message += "⏳ Ожидает оплаты.\n"
    # else:
    #     message += "ℹ️ Дополнительная информация уточняется.\n"  # Обработка неизвестных статусов

    return message
    


@router.callback_query(F.data == "manager_update_status")
async def ask_for_user_code(callback: CallbackQuery, state: FSMContext):
    """Запрашивает у менеджера user_code пользователя."""
    await callback.message.answer("Введите код заказа, статус которого хотите изменить:")
    await state.set_state(ManagerStates.waiting_for_order_code)
    await callback.answer()


@router.message(ManagerStates.waiting_for_order_code)
async def process_order_code(message: Message, state: FSMContext, db: Database):
    """Обрабатывает введенный order_code."""
    try:
        order_code = message.text
    except ValueError:
        await message.answer("Некорректный order_code. Пожалуйста, введите корректное значение.")
        return

    await state.clear()  # Сбрасываем состояние

    # Получаем активные заказы пользователя
    order = await db.get_order_by_code(order_code)

    if order:
        await state.update_data(order_code=order_code)
        order_message = f'Данные заказа({order_code}):\n'
        order_info = format_order_for_telegram(order)
        order_message += order_info
        print(order_message)
        await message.answer(f"{order_message} Укажите новый статус заказа:\n", 
                             reply_markup=order_status_keyboard)
    else:
        await message.answer(f"Нет данных по заказу {order_code}")


@router.message(ManagerStates.waiting_for_user_code)
async def process_user_tg_id(message: Message, state: FSMContext, db: Database):
    """Обрабатывает введенный user_code и показывает активные заказы."""
    try:
        user_code = message.text
    except ValueError:
        await message.answer("Некорректный user_code. Пожалуйста, введите корректное значение.")
        return

    await state.clear()  # Сбрасываем состояние

    # Получаем активные заказы пользователя
    orders = await db.get_active_orders_by_user_code(user_code)

    if orders:
        order_message = f'Активные заказы пользователя ({user_code}):\n'
        codes = []
        for order in orders:
            codes.append(order.id)
            order_info = format_order_for_telegram(order)
            order_message += order_info
            order_message += '\n'
        print(order_message)
        await message.answer(
            f"Активные заказы пользователя ({user_code}): {order_message}")
            
        await message.answer(
    "Выберите заказ, статус которого хотите изменить:",
    reply_markup=create_inline_keyboard(codes)
)
    else:
        await message.answer(f"Нет активных заказов для пользователя с tg_id {user_code}")



@router.callback_query(F.data.startswith(CALLBACK_DATA_PREFIX))
async def process_order_selection(callback: CallbackQuery, state: FSMContext, db: Database):
    """
    Обработчик нажатия на кнопки с code заказов.
    """
    order_code = callback.data[len(CALLBACK_DATA_PREFIX):]  # Извлекаем code заказа из callback_data

    order = await db.get_order_by_code(order_code=order_code)
    if order:
        await state.update_data(order_code=order_code)
        order_info = format_order_for_telegram(order)
        # print(order_info)
        await callback.message.answer(f"Информация о заказе ({order_code}) : \n{order_info}") # Уведомление вверху экрана
        await callback.message.answer(f"Укажите новый статус заказа:", reply_markup=order_status_keyboard)
    else:
        await callback.message.answer(f"Нет данных по заказу {order_code}.")
    await callback.answer() #  Обязательно отвечаем на callback query, даже если ничего не делаем



@router.callback_query(lambda c: c.data.startswith('status_'))
async def process_status_selection(callback: CallbackQuery, state: FSMContext, db: Database):
    """
    Обработчик для выбора статуса заказа.
    """
    selected_status = callback.data[len('status_'):] # Извлекаем статус из callback_data
    data = await state.get_data()
    order_code = data.get('order_code')

    if not order_code:
        await callback.answer("Не найден order_code в state. Пожалуйста, выберите заказ заново.")
        return

    # Обновляем статус заказа в базе данных
    success = await db.update_order_status(order_code, selected_status)

    if success:
        await callback.message.answer(f"Статус заказа {order_code} успешно изменен на: {selected_status}")
    else:
        await callback.message.answer(f"Не удалось обновить статус заказа {order_code}.")

    await callback.answer() #Отвечаем на callback
    await callback.message.answer('Основное меню:', reply_markup=manager_keyboard)
 
# Основной обработчик callback-запросов
@router.callback_query(F.data.startswith("manager_orders:"))  # Ловим callback, начинающиеся с 'manager_'
async def process_manager_callback(callback: CallbackQuery, db: Database, bot: Bot):

    order_status = callback.data.split(":")[1]

    orders = await db.get_orders_by_status(order_status)
    if orders:
        message_text = ""
        messages = []  # Список для хранения частей сообщений
        for order in orders:
            order_data = format_order_data(order)
            if len(message_text) + len(order_data) > 4096:
                # Текущее сообщение заполнено, отправляем его и начинаем новое
                messages.append(message_text)
                message_text = order_data  # Начинаем новое сообщение с текущего заказа
            else:
                message_text += order_data  # Добавляем заказ к текущему сообщению
        # Отправляем последнее сообщение (если оно не пустое)
        if message_text:
            messages.append(message_text)

        # Отправляем сообщения по частям
        for message in messages:
            await callback.message.answer(message)

    else:
        await callback.message.answer("Нет заказов с указанным статусом.")
    await callback.answer()

