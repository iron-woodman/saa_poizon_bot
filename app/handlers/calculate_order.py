import datetime
import logging
from aiogram.fsm.state import State, StatesGroup
from aiogram import types, F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, 
                           InlineKeyboardMarkup, FSInputFile)
from app.keyboards.main_kb import main_keyboard
from app.keyboards.calculate_order_kb import (order_type_keyboard, calculate_category_keyboard, 
                                              registration_keyboard, opt_keyboard)
# from app.utils.currency import get_currency_cny
from app.config import MANAGER_TELEGRAM_ID
from app.database.database import Database

# Настройка логирования
logging.basicConfig(level=logging.INFO, encoding='utf-8')

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
    
    await callback_query.message.answer("Выберите категорию товара:", reply_markup=calculate_category_keyboard)
    await state.set_state(OrderState.choosing_good)
    await callback_query.answer()


@router.callback_query(F.data == 'wholesale')
async def process_order_type(callback_query: CallbackQuery, state: FSMContext):
    order_type = callback_query.data
    await state.update_data(order_type=order_type)
    await callback_query.message.answer(
        (
            "Вы выбрали оптовый тип заказа!\n"
            "Для расчета стоимости на оптовый заказ свяжитесь пожалуйста с нашим менеджером "
            "или ознакомьтесь с текущим прайсом."),
            reply_markup= opt_keyboard
        )

    await callback_query.answer()
    

@router.callback_query(F.data == "opt_ask_manager")
async def send_opt_request_to_manager(callback_query: CallbackQuery, bot: Bot, db: Database):
    """Sends opt price calculateion request to manager"""

    tg_id = callback_query.from_user.id
    user = await db.get_user_by_tg_id(tg_id)

    # print(f"Пользователь {user.telegram_link if user.telegram_link else '' } \
    #                                 ({user.unique_code}) запросил расчет оптового заказа.")
    if user:
        await bot.send_message(chat_id=MANAGER_TELEGRAM_ID, 
                                text=f"Пользователь {user.telegram_link if user.telegram_link else '' } \
                                    ({user.unique_code}) запросил расчет оптового заказа.")
        await callback_query.message.answer("Ваш запрос уже у нашего менеджера. Скоро он с Вами свяжется.")

    await callback_query.answer() # Acknowledge callback

@router.callback_query(F.data == "shipping_cost")
async def send_shipping_cost_document(callback_query: CallbackQuery, bot: Bot):
    """Sends the shipping cost document to the user."""
    document = FSInputFile("data/IR1047.xlsx") # REPLACE with correct path
    await bot.send_document(callback_query.from_user.id, document=document, 
                            caption="Шаблон для расчета стоимости доставки и упаковки")
    await callback_query.answer() # Acknowledge callback

@router.callback_query(OrderState.choosing_good, F.data.startswith("calculate_category:"))
async def process_good_type(callback_query: CallbackQuery, state: FSMContext, db: Database):
    good_type = callback_query.data.split(":")[1]
    await state.update_data(good_type=good_type)

 # Получаем текущий курс юаня к рублю из БД
    cny_to_rub = await db.get_exchange_rate("cny_to_rub")
    if cny_to_rub is None:
        logging.error("Не удалось получить курс юаня из БД.")
        await callback_query.message.answer("Не удалось получить курс юаня из БД.")
        await state.clear()
        await callback_query.answer()
        return None
    
    await state.update_data(cny_to_rub=cny_to_rub)

    text = (
            "Введите сумму товара в CNY:\n\n"
            f"Курс на сегодня ({datetime.datetime.now().strftime('%d.%m.%Y')}):\n"
            f"👉 ¥1 = {cny_to_rub} ₽\n"
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
async def process_delivery_type(callback_query: CallbackQuery, state: FSMContext, db: Database):
    delivery_type = callback_query.data
    await state.update_data(delivery_type=delivery_type)

    user_data = await state.get_data()  # Get all collected data
    order_type = user_data.get('order_type')
    good_type = user_data.get('good_type')
    price = user_data.get('price')
    cny_to_rub = user_data.get('cny_to_rub')

    if delivery_type == "air_delivery":
        delivery_name = "Авиаэкспресс"
    else:
        delivery_name = "Автоэкспресс"

    
    # Получаем стоимость доставки в юанях из БД
    delivery_price_rub = await db.get_delivery_price(good_type, delivery_name)
    if delivery_price_rub is None:
        await callback_query.message.answer(
            f"Не удалось получить стоимость доставки для категории '{good_type}' и типа '{delivery_name}' из БД.")
        await state.clear()
        await callback_query.answer()
        logging.error(f"Не удалось получить цену доставки для категории '{good_type}' и типа '{delivery_name}' из БД.")
        return None

    price_rub = price * cny_to_rub
    total_price = price_rub + delivery_price_rub

    # Create the final order information message
    order_info = (
        f"Тип заказа: {order_type}\n"
        f"Категория товара: {good_type}\n"
        f"Цена товара: {price} CNY\n"
        f"Цена товара в рублях: {price_rub} руб.\n"
        f"Тип доставки: {delivery_name}\n"
        f"Стоимость доставки: {delivery_price_rub} руб.\n"
        f"Итоговая стоимость: {total_price} руб.\n"

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
async def process_confirm_order(callback_query: CallbackQuery, state: FSMContext, db: Database):

    tg_id = callback_query.from_user.id
    # Проверяем, существует ли пользователь с таким telegram ID
    existing_user = await db.get_user_by_tg_id(tg_id)  # Теперь используем db
    if not existing_user:  #Исправлено: если пользователя нет, то предлагаем зарегистрироваться.
         # Implement order confirmation logic here (e.g., send order details to admin, etc.)
         await callback_query.message.answer(
        "Для начала необходимо пройти простую процедуру регистрации в системе.",
          reply_markup=registration_keyboard)
    else:
         await callback_query.message.answer(
        "Вы уже зарегистрированы в системе и можете оформить заказ.",
          reply_markup=main_keyboard)
   
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
