from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Клавиатура корзины заказа
admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Активные заказы 📦", callback_data="active_orders")],
    [InlineKeyboardButton(text="Все заказы 🧾", callback_data="all_orders")],
])

# Клавиатура статусов заказа (для изменения статуса)
order_status_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создан", callback_data="status_Создан")],
    [InlineKeyboardButton(text="Оплачен", callback_data="status_Оплачен")],
    [InlineKeyboardButton(text="В обработке", callback_data="status_В обработке")],
    [InlineKeyboardButton(text="Отправлен", callback_data="status_Отправлен")],
    [InlineKeyboardButton(text="Завершен", callback_data="status_Завершен")],
    [InlineKeyboardButton(text="Отменен", callback_data="status_Отменен")],
])


# ID обработчика (можно любой, но уникальный для роутера)
CALLBACK_DATA_PREFIX = "order_id_"

def create_inline_keyboard(order_codes: list[str]) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для Telegram бота на основе списка ID заказов.

    Args:
        order_ids: Список ID заказов (например, ["A001", "B256", "Z999"]).

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура для отправки в Telegram.
    """

    builder = InlineKeyboardBuilder()
    for order_code in order_codes:
        button_text = order_code  # Текст кнопки - ID заказа
        callback_data = CALLBACK_DATA_PREFIX + order_code # Префикс для callback_data
        builder.button(text=button_text, callback_data=callback_data)

    builder.adjust(1)  # Автоматически распределяем кнопки по строкам, по 1 в ряд (можно изменить)
    return builder.as_markup()