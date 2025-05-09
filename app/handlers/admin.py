import os
import json
import logging
from aiogram import F, Router, Bot
from aiogram.types import (Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, Document,
    InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, List

from app.database.database import Database
from app.database.models import Order
from app.keyboards.admin_kb import (create_inline_keyboard, CALLBACK_DATA_PREFIX, 
                                    order_status_keyboard, admin_keyboard)

# Получите логгер
logger = logging.getLogger(__name__)

router = Router()


# FSM для запроса telegram_id
class AdminStates(StatesGroup):
    waiting_for_user_tg_id = State()


def format_order_for_telegram(order: Order) -> str:
    """
    Форматирует информацию о заказе для отправки в Telegram-боте.
    Добавляет эмодзи для улучшения восприятия.
    """

    message = f"📦 *Заказ №{order.order_code}*\n\n"  # Используем order_code вместо order.id
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
    if order.status == "Оплачен":
        message += "✅ Заказ оплачен, ожидаем подтверждения.\n"
    elif order.status == "В обработке":
        message += "🛠️ Заказ в обработке.\n"
    elif order.status == "Отправлен":
        message += "🚀 Заказ отправлен!\n"
    elif order.status == "Завершен":
        message += "🎉 Заказ завершен. Спасибо за покупку!\n"
    elif order.status == "Отменен":
        message += "❌ Заказ отменен.\n"
    elif order.status == "Создан":
        message += "⏳ Ожидает оплаты.\n"
    else:
        message += "ℹ️ Дополнительная информация уточняется.\n"  # Обработка неизвестных статусов

    return message



@router.callback_query(F.data == "active_orders")
async def ask_for_user_tg_id(callback: CallbackQuery, state: FSMContext):
    """Запрашивает у администратора telegram_id пользователя."""
    await callback.message.answer("Введите telegram ID пользователя, для которого нужно найти активные заказы:")
    await state.set_state(AdminStates.waiting_for_user_tg_id)
    await callback.answer()


@router.message(AdminStates.waiting_for_user_tg_id)
async def process_user_tg_id(message: Message, state: FSMContext, db: Database):
    """Обрабатывает введенный telegram_id и показывает активные заказы."""
    try:
        user_tg_id = int(message.text)
    except ValueError:
        await message.answer("Некорректный telegram ID. Пожалуйста, введите число.")
        return

    await state.clear()  # Сбрасываем состояние

    # Получаем активные заказы пользователя
    orders = await db.get_active_orders_by_tg_id(user_tg_id)

    if orders:
        order_message = f'Активные заказы пользователя ({user_tg_id}):\n'
        codes = []
        for order in orders:
            codes.append(order.order_code)
            order_info = format_order_for_telegram(order)
            order_message += order_info
            order_message += '\n'
        print(order_message)
        await message.answer(
            f"Активные заказы пользователя ({user_tg_id}): {order_message}")
            
        await message.answer(
    "Выберите заказ, статус которого хотите изменить:",
    reply_markup=create_inline_keyboard(codes)
)
    else:
        await message.answer(f"Нет активных заказов для пользователя с tg_id {user_tg_id}")


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
    await callback.message.answer('Основное меню:', reply_markup=admin_keyboard)

@router.callback_query(F.data == "all_orders")
async def show_all_orders(callback: CallbackQuery, db: Database):
    """Обработчик для кнопки 'Все заказы'."""
    tg_id = callback.from_user.id
    orders = await db.get_all_orders_by_tg_id(tg_id)
    if orders:
        order_message = f'заказы пользователя {tg_id} (полный список):\n'
        for order in orders:
            order_info = format_order_for_telegram(order)
            order_message += order_info
            order_message += '\n'
        print(order_message)
        await callback.message.answer(
            f"Информация о заказах пользователя {tg_id}: {order_message}") # Уведомление вверху экрана
    
    await callback.answer()
    await callback.message.answer('Основное меню:', reply_markup=admin_keyboard)


@router.callback_query(F.data == "update_prices")
async def show_upload_prompt(callback: CallbackQuery):
    """Обработчик для кнопки 'Загрузить цены'"""
    await callback.message.answer("Загрузите JSON файл для обновления цен доставки и курса валют.")
    await callback.answer()  # Отправляем подтверждение, что callback обработан


@router.message(F.document)
async def handle_document(message: Message, bot: Bot, db: Database):
    """Обработчик для загрузки JSON файла с ценами и курсом."""
    document: Document = message.document # Исправлено: Получение document из message, а не из callback
    if document.mime_type == 'application/json':
        # Скачиваем файл
        file_id = document.file_id
        file = await bot.get_file(file_id)
        file_path_dl = file.file_path
        file_path = f"{document.file_name}"  # Убираем временное имя (оно будет создано при скачивании)
        await bot.download_file(file_path_dl, file_path)

        try:
            # Обновляем данные в БД
            success = await update_data_from_json(file_path, db) # Передаем db
            if success:
                await message.reply("Цены доставки и курс валют успешно обновлены!")
            else:
                await message.reply("Ошибка при обновлении данных. Проверьте формат файла.")
        except Exception as e:
            logger.error(f"Ошибка при обработке JSON файла: {e}", exc_info=True)
            await message.reply("Произошла ошибка при обработке JSON файла. Проверьте его формат.")
        finally:
            try:
                os.remove(file_path) # Пытаемся удалить файл
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {file_path}: {e}") # Логируем, если не удалось удалить
    else:
        await message.reply("Пожалуйста, загрузите JSON файл.")


async def update_data_from_json(file_path: str, db: Database) -> bool:
    """Обновляет курс валют и цены доставки из JSON файла."""
    try:
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)

        # Обновление курса юаня
        cny_to_rub = data['exchange_rate']['cny_to_rub']
        await db.add_or_update_exchange_rate("cny_to_rub", cny_to_rub)

        # Обновление цен доставки
        for delivery_type, category_prices in data['delivery_types'].items():
            for category, price in category_prices.items():
                await db.add_or_update_delivery_price(category, delivery_type, price)

        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных из JSON: {e}", exc_info=True)
        return False