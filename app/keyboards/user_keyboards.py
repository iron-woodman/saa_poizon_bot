from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,  InlineKeyboardMarkup, InlineKeyboardButton

# --- Клавиатуры ---

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=" ⚙️ Меню"),
            KeyboardButton(text=" ❓ Помощь"),
        ]
    ],
    resize_keyboard=True,
)

user_inline_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Рассчитать стоимость 💰", callback_data="calculate_price")],
    [InlineKeyboardButton(text="✅ Оформить заказ ✅", callback_data="place_order")],
    [InlineKeyboardButton(text="🔎 Отследить заказ 🔎", callback_data="track_order")],
    [InlineKeyboardButton(text="🆘 Запросить помощь 🆘", callback_data="request_help")],
    [InlineKeyboardButton(text="💬 Отзывы о нашей работе ↗️", callback_data="reviews")],
])


order_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍 Розничный", callback_data="retail"),
            InlineKeyboardButton(text="📦 Оптовый", callback_data="wholesale")
        ],
        [
            InlineKeyboardButton(text="🔙 ГЛАВНОЕ МЕНЮ ↩️", callback_data="main_menu")
        ]
    ])





