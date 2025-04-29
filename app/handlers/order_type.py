import datetime
from aiogram.fsm.state import State, StatesGroup
from aiogram import types, F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, 
                           InlineKeyboardMarkup, FSInputFile)
from app.keyboards.main_kb import main_keyboard
from app.keyboards.calculate_order_kb import (order_type_keyboard, get_category_keyboard, 
                                              registration_keyboard)
from app.utils.currency import get_currency_cny
from app.config import MANAGER_TELEGRAM_ID


router = Router()


# FSM States
class OrderState(StatesGroup):
    choosing_order_type = State()  # Опт или розница
    choosing_good = State()        # Выбор товара
    waiting_price = State()       # Ввод стоимости
    choosing_delivery = State()    # Выбор доставки


@router.callback_query(F.data == 'calculate_price')
async def calculate_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Выберите тип заказа:", reply_markup=order_type_keyboard
    )
    await state.set_state(OrderState.choosing_order_type)
    await callback.answer()

@router.callback_query(OrderState.choosing_order_type, F.data == 'retail')
async def process_order_type(callback_query: CallbackQuery, state: FSMContext):
    order_type = callback_query.data
    await state.update_data(order_type=order_type)
    await callback_query.message.answer("Вы выбрали розничный расчет!")
    
    keyboard = await get_category_keyboard()
    await callback_query.message.answer("Выберите категорию товара:", reply_markup=keyboard)
    await state.set_state(OrderState.choosing_good)
    await callback_query.answer()



@router.callback_query(F.data == 'wholesale')
async def process_order_type(callback_query: CallbackQuery, state: FSMContext):
    order_type = callback_query.data
    await state.update_data(order_type=order_type)

    opt_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧑‍💼 Связаться с менеджером",
                    url=f"tg://user?id={MANAGER_TELEGRAM_ID}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 Стоимость доставки и упаковки",
                    callback_data="shipping_cost"
                ),
            ],
        ]
    )

    await callback_query.message.answer(
        (
            "Вы выбрали оптовый расчет!\n"
            "Для расчета стоимости на оптовый заказ свяжитесь пожалуйста с нашим менеджером"),
            reply_markup= opt_keyboard
        )

    await callback_query.answer()

@router.callback_query(F.data == "shipping_cost")
async def send_shipping_cost_document(callback_query: CallbackQuery, bot: Bot):
    """Sends the shipping cost document to the user."""
    document = FSInputFile("data/IR1047.xlsx") # REPLACE with correct path
    await bot.send_document(callback_query.from_user.id, document=document, caption="Шаблон для расчета стоимости доставки и упаковки")
    await callback_query.answer() # Acknowledge callback




@router.callback_query(OrderState.choosing_good, F.data.in_([
    "clothes", "outerwear", "underwear", "summer_shoes", "winter_shoes",
    "small_bags", "big_bags", "perfume", "other_products"
]))
async def process_good_type(callback_query: CallbackQuery, state: FSMContext):
    good_type = callback_query.data
    await state.update_data(good_type=good_type)
    text = (
            "Введите сумму товара в CNY:\n\n"
            f"🇨🇳 Курс на сегодня ({datetime.datetime.now().strftime('%d.%m.%Y')}):\n"
            f"👉 ¥1 = {get_currency_cny()} ₽\n"
        )

    await callback_query.message.answer(text)
    await state.set_state(OrderState.waiting_price)
    await callback_query.answer()



@router.message(OrderState.waiting_price, F.text)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)

        text = (
            f"Сумма товара в CNY: {price}\n"
            f"Выберите тип доставки:"
        )

        delivery_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✈️ Авиаэкспресс", callback_data="air_delivery"),
                InlineKeyboardButton(text="🚛 Автоэкспресс", callback_data="express_delivery"),
            ]
        ])

        await message.answer(text, reply_markup=delivery_keyboard)
        await state.set_state(OrderState.choosing_delivery)
    except ValueError:
        await message.answer("Пожалуйста, введите числовое значение для суммы товара.")



@router.callback_query(OrderState.choosing_delivery, F.data.in_(['air_delivery', 'express_delivery']))
async def process_delivery_type(callback_query: CallbackQuery, state: FSMContext):
    delivery_type = callback_query.data
    await state.update_data(delivery_type=delivery_type)

    user_data = await state.get_data()  # Get all collected data
    order_type = user_data.get('order_type')
    good_type = user_data.get('good_type')
    price = user_data.get('price')

    if delivery_type == "air_delivery":
        delivery_name = "Авиаэкспресс"
    else:
        delivery_name = "Автоэкспресс"

    # Create the final order information message
    order_info = (
        f"Тип заказа: {order_type}\n"
        f"Категория товара: {good_type}\n"
        f"Сумма: {price} CNY\n"
        f"Тип доставки: {delivery_name}"
    )

    # Create the inline keyboard for post-order actions
    post_order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Рассчитать другой заказ", callback_data="new_order"),
            InlineKeyboardButton(text="Оформить заказ", callback_data="confirm_order"),
        ],
        [
            InlineKeyboardButton(text="⬅ Назад", callback_data="back"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
        ],
    ])

    await callback_query.message.answer(order_info, reply_markup=post_order_keyboard)

    await callback_query.answer()

@router.callback_query(F.data == "new_order")
async def process_new_order(callback_query: CallbackQuery, state: FSMContext):
    # Reset the state and start a new order calculation
    await state.clear()
    await calculate_price(callback_query, state)  # Start over with calculate_price
    await callback_query.answer()


@router.callback_query(F.data == "confirm_order")
async def process_confirm_order(callback_query: CallbackQuery, state: FSMContext):
    # Implement order confirmation logic here (e.g., send order details to admin, etc.)
    await callback_query.message.answer(
        "Для начала необходимо пройти простую процедуру регистрации в системе.",
          reply_markup=registration_keyboard)
    await state.clear()  # Clear state after order confirmation
    await callback_query.answer()


@router.callback_query(F.data == "back")
async def process_back(callback_query: CallbackQuery, state: FSMContext):
    # Go back to the delivery options selection
    await callback_query.answer("Вы вернулись к выбору типа доставки")

    user_data = await state.get_data()
    price = user_data.get('price')

    text = (
        f"Сумма товара в CNY: {price}\n"
        f"Выберите тип доставки:"
    )

    delivery_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✈ Авиаэкспресс", callback_data="air_delivery"),
                InlineKeyboardButton(text="🚛 Автоэкспресс", callback_data="express_delivery"),
            ]
        ])

    await callback_query.message.edit_text(text, reply_markup=delivery_keyboard)
    await state.set_state(OrderState.choosing_delivery)


@router.callback_query(F.data == "cancel")
async def process_cancel(callback_query: CallbackQuery, state: FSMContext):
    # Cancel the order and clear the state
    await callback_query.message.answer("Заказ отменен.")
    await callback_query.message.delete() #remove message
    await state.clear()
    await callback_query.answer()
