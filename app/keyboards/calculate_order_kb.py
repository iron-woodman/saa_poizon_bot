from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


order_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍 Розничный", callback_data="retail"),
            InlineKeyboardButton(text="📦 Оптовый", callback_data="wholesale")
        ],
        [
            InlineKeyboardButton(text="🔙 ГЛАВНОЕ МЕНЮ ↩️", callback_data="main_menu")
        ]
    ])

retail_category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍 Розничный", callback_data="retail"),
            InlineKeyboardButton(text="📦 Оптовый", callback_data="wholesale")
        ],
        [
            InlineKeyboardButton(text="🔙 ГЛАВНОЕ МЕНЮ ↩️", callback_data="main_menu")
        ]
    ])




async def get_category_keyboard():
    """Создает inline-клавиатуру с заданными категориями."""

    buttons = [
        InlineKeyboardButton(text="Одежда", callback_data="clothes"),
        InlineKeyboardButton(text="Верхняя одежда", callback_data="outerwear"),
        InlineKeyboardButton(text="Нижнее белье", callback_data="underwear"),
        InlineKeyboardButton(text="Летняя обувь", callback_data="summer_shoes"),
        InlineKeyboardButton(text="Зимняя обувь", callback_data="winter_shoes"),
        InlineKeyboardButton(text="Кошельки и сумки", callback_data="small_bags"),
        InlineKeyboardButton(text="Парфюм", callback_data="perfume"),
        InlineKeyboardButton(text="Большие сумки", callback_data="big_bags"),
    ]

    # Кнопка "Уточнить другие товары?" на всю ширину
    other_products_button = InlineKeyboardButton(text="Уточнить другие товары?", 
                                                 callback_data="other_products")

    # Кнопки "Назад" и "Отмена"
    back_button = InlineKeyboardButton(text="⬅️ Назад", callback_data="order_type_back")
    cancel_button = InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")


    # Разделяем основные кнопки на ряды по row_width
    row_width = 2
    keyboard_rows = [buttons[i:i + row_width] for i in range(0, len(buttons), row_width)]

    # Добавляем кнопку "Уточнить другие товары?" в отдельный ряд
    keyboard_rows.append([other_products_button])

    # Добавляем кнопки "Назад" и "Отмена" в один ряд
    keyboard_rows.append([back_button, cancel_button])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    return keyboard


order_management_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Собрать заказ", callback_data="assemble_order"),
        ],
        [
            InlineKeyboardButton(text="✏️ Изменить данные", callback_data="registration"),
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"),
        ],
    ]
)



delivery_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚛 Автоэкспресс", callback_data="express_delivery"),
            InlineKeyboardButton(text="✈️ Авиаэкспресс", callback_data="air_delivery"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
        ]
    ])

registration_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="👤 Регистрация", callback_data="registration"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
    ]
])