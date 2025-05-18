from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Клавиатура категорий товаров (сгруппировано в 2 столбца)
category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="👚 Одежда", callback_data="category:Одежда"),
        InlineKeyboardButton(text="🧥 Верхняя одежда", callback_data="category:Верхняя одежда")
    ],
    [
        InlineKeyboardButton(text="🩲 Нижнее белье", callback_data="category:Нижнее белье"),
        InlineKeyboardButton(text="🩴 Летняя обувь", callback_data="category:Летняя обувь")
    ],
    [
        InlineKeyboardButton(text="🥾 Зимняя обувь", callback_data="category:Зимняя обувь"),
        InlineKeyboardButton(text="💼 Кошельки", callback_data="category:Кошельки")
    ],
    [
        InlineKeyboardButton(text="🌸 Парфюм", callback_data="category:Парфюм"),
        InlineKeyboardButton(text="👜 Большие сумки", callback_data="category:Большие сумки")
    ],
])

# Клавиатура выбора способа доставки
delivery_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🚛 Автоэкспресс", callback_data="delivery:Автоэкспресс"),
        InlineKeyboardButton(text="✈️ Авиаэкспресс", callback_data="delivery:Авиаэкспресс")
    ],
    [
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_size"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")
    ],  
])

# Клавиатура корзины заказа
cart_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Продолжить оформление", callback_data="continue_checkout")],
    # [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_another_item")],
    [InlineKeyboardButton(text="🗑️ Удалить товары", callback_data="remove_items")],
    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
])

# Клавиатура подтверждения заказа
confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data="confirm_payment")],
    [InlineKeyboardButton(text="🏷️ Использовать промокод", callback_data="use_promocode")],
    [
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_cart"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")
    ], 
])

# Клавиатура отслеживания заказа
track_order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔍 Проверить статус", callback_data="check_status")],
    [InlineKeyboardButton(text="📜 История ваших заказов", callback_data="order_history")],
    [InlineKeyboardButton(text="ℹ️ Информация о статусах", callback_data="status_info")],
])
