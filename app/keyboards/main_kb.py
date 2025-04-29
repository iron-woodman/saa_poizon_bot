from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,  InlineKeyboardMarkup, 
                           InlineKeyboardButton)
from app.config import HELP_URL

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
    [InlineKeyboardButton(text="✅ Оформить заказ ✅", callback_data="assemble_order")],
    [InlineKeyboardButton(text="🔎 Отследить заказ 🔎", callback_data="track_order")],
    [InlineKeyboardButton(text="🆘 Запросить помощь 🆘", callback_data="request_help")],
    [InlineKeyboardButton(text="💬 Отзывы о нашей работе ↗️", callback_data="reviews")],
])


otziv_inline_menu = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="⭐️ Перейти на сайт", url=HELP_URL, callback_data="go_to_feedback"),
    ]
])
