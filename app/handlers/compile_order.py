import os
import logging
import datetime
from aiogram import F, Router, Bot, types
from aiogram.types import (Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.config import MANAGER_TELEGRAM_ID, PAY_SCREENS_DIR  # Убедитесь, что у вас настроен MANAGER_TELEGRAM_ID
from app.utils.regex import (normolize_phone_number, validate_international_phone_number_basic,
                                  validate_full_name)
from app.keyboards.compile_order_kb import (delivery_keyboard, category_keyboard, 
                                                  cart_keyboard, confirmation_keyboard, 
                                                  track_order_keyboard)
from app.keyboards.calculate_order_kb import registration_keyboard
from app.utils.currency import get_currency_cny
from app.database.database import Database
# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем роутер
router = Router()

# --- Состояния FSM ---
class OrderForm(StatesGroup):
    waiting_for_category = State()
    waiting_for_price = State()
    waiting_for_size = State()
    waiting_for_color = State()
    waiting_for_link = State()
    waiting_for_delivery_method = State()
    waiting_for_payment_screenshot = State() # Добавлено состояние для скриншота оплаты
    waiting_for_promocode = State()  # Добавлено состояние для промокода



# --- Обработчики ---

@router.callback_query(F.data == "assemble_order")
async def start_order_assembly(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """
    Обработчик нажатия на кнопку "Собрать заказ".
    """
    tg_id = callback_query.from_user.id
    print(f'{tg_id=}')
    # Проверяем, существует ли пользователь с таким telegram ID
    existing_user = await db.get_user_by_tg_id(tg_id)  # Теперь используем db
    if not existing_user:  #Исправлено: если пользователя нет, то предлагаем зарегистрироваться.
        await callback_query.message.answer(
            "Вы еще не зарегистрированы в системе! Пройдите простую регистрацию.",
            reply_markup=registration_keyboard
        )
        await state.clear() #Сбрасываем состояние
    else:
        await callback_query.message.answer(
            "Выберите категорию товара:\n- От выбора категории зависит стоимость доставки вашего товара",
            reply_markup=category_keyboard
        )
        await state.set_state(OrderForm.waiting_for_category)
    await callback_query.answer()  # Отвечаем на callback, чтобы убрать часы


@router.callback_query(OrderForm.waiting_for_category, F.data.startswith("category:"))
async def process_category(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора категории товара.
    """
    category = callback_query.data.split(":")[1]
    if category == "back":
        await callback_query.message.answer("Выберите категорию товара:\n- От выбора категории зависит стоимость доставки вашего товара",
                                         reply_markup=category_keyboard)
        await state.set_state(OrderForm.waiting_for_category)
        await callback_query.answer()  # Отвечаем на callback, чтобы убрать часы
    else:
        await state.update_data(category=category)
        await callback_query.message.answer(f"Вы выбрали категорию: {category}")

        text = (
            "Введите сумму товара в CNY:\n\n"
            f"🇨🇳 Курс на сегодня ({datetime.datetime.now().strftime('%d.%m.%Y')}):\n"
            f"👉 ¥1 = {get_currency_cny()} ₽\n"
        )

        await callback_query.message.answer(text)
        await state.set_state(OrderForm.waiting_for_price)
        await callback_query.answer()


@router.message(OrderForm.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    """
    Обработчик ввода суммы товара.
    """
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer(
            '''
📏 Размер товара:\n
Укажите размер Вашего товара, чтобы мы не ошиблись с заказом.\n
Пример: XS или 52 для одежды 👚\n 41 или 37,5 для обуви 👟 . \n
Если товар продается без размера, то напишите слово "НЕТ".
''')
        await state.set_state(OrderForm.waiting_for_size)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму в формате числа (например, 123.45)")


@router.message(OrderForm.waiting_for_size)
async def process_size(message: Message, state: FSMContext):
    """
    Обработчик ввода размера товара.
    """
    size = message.text
    await state.update_data(size=size)
    await message.answer("Введите цвет товара:")
    await state.set_state(OrderForm.waiting_for_color)


@router.message(OrderForm.waiting_for_color)
async def process_color(message: Message, state: FSMContext):
    """
    Обработчик ввода цвета товара.
    """
    color = message.text
    await state.update_data(color=color)
    await message.answer("Введите ссылку на товар:")
    await state.set_state(OrderForm.waiting_for_link)


@router.message(OrderForm.waiting_for_link)
async def process_link(message: Message, state: FSMContext):
    """
    Обработчик ввода ссылки на товар.
    """
    link = message.text
    await state.update_data(link=link)
    await message.answer("Доставка заказа:\nВыберите наиболее подходящий способ доставки Вашего заказа:\n",
                         reply_markup=delivery_keyboard)
    await state.set_state(OrderForm.waiting_for_delivery_method)

@router.callback_query(OrderForm.waiting_for_delivery_method, F.data.startswith("delivery:"))
async def process_delivery_method(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """
    Обработчик выбора способа доставки.
    """
    delivery_method = callback_query.data.split(":")[1]
    await state.update_data(delivery_method=delivery_method)
    await callback_query.message.answer(f"Вы выбрали способ доставки: {delivery_method}")

    # Получаем данные пользователя
    user = await db.get_user_by_tg_id(callback_query.from_user.id)
    user_data = {
        'full_name': user.full_name,
        'phone_number': user.phone_number,
        'address': user.main_address
    } 

    # Формируем сообщение для корзины
    data = await state.get_data()
    category = data.get('category', 'Не указано')
    size = data.get('size', 'Не указано')
    color = data.get('color', 'Не указано')
    link = data.get('link', 'Не указано')
    price = data.get('price', 'Не указано')
    delivery_method = data.get('delivery_method', 'Не указано')
    total_price = price * float(get_currency_cny()) #Рассчет стоимости

    cart_message = f"️КОРЗИНА ЗАКАЗОВ ️\n" \
                   f"ФИО: {user_data['full_name']}\n" \
                   f"Контакт: {user_data['phone_number']}\n" \
                   f"Адрес: {user_data['address']}\n" \
                   f"‍️ВЫБРАННЫЕ ТОВАРЫ ‍️\n" \
                   f"➀ Категория товара: {category}\n" \
                   f"➁ Размер товара: {size}\n" \
                   f"➂ Цвет товара: {color}\n" \
                   f"➃ Ссылка на товар: {link}\n" \
                   f"➄ Стоимость товара: {price:.2f}₽ - ({delivery_method})\n" \
                   f"ОБЩАЯ СТОИМОСТЬ: {total_price:.2f}₽\n" \

    await callback_query.message.answer(cart_message, reply_markup=cart_keyboard)
    await callback_query.answer()

@router.callback_query(F.data == "back_to_size")
async def back_to_size(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик для кнопки "Назад" из delivery_keyboard.
    Возвращает к запросу размера товара.
    """
    await callback_query.message.answer("️ Размер товара:\nУкажите размер Вашего товара, чтобы мы не ошиблись с заказом\nПример: ️ XS или 52 (если одежда) ️ 41 или 37,5 (если обувь)")
    await state.set_state(OrderForm.waiting_for_size)
    await callback_query.answer()

@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик для кнопки "Отмена".
    Прерывает процесс оформления заказа и сбрасывает состояние.
    """
    await callback_query.message.answer("Оформление заказа отменено.")
    await state.clear()
    await callback_query.answer()

@router.callback_query(F.data == "continue_checkout")
async def process_continue_checkout(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """
    Обработчик нажатия на кнопку "Продолжить оформление".
    """

    # Получаем данные пользователя
    user = await db.get_user_by_tg_id(callback_query.from_user.id)
    user_data = {
        'full_name': user.full_name,
        'phone_number': user.phone_number,
        'address': user.main_address
    } 

    # Формируем сообщение для подтверждения заказа
    data = await state.get_data()
    category = data.get('category', 'Не указано')
    size = data.get('size', 'Не указано')
    color = data.get('color', 'Не указано')
    link = data.get('link', 'Не указано')
    price = data.get('price', 'Не указано')
    delivery_method = data.get('delivery_method', 'Не указано')
    total_price = price * get_currency_cny() #Рассчет стоимости

    confirmation_message = f"ПОДТВЕРЖДЕНИ ЗАКАЗА\n" \
                           f"ФИО: {user_data['full_name']}\n" \
                           f"Контакт: {user_data['phone_number']}\n" \
                           f"Адрес: {user_data['address']}\n" \
                           f"‍️ СОБРАННЫЕ ТОВАРЫ ‍️\n" \
                           f"➀ Категория товара: {category}\n" \
                           f"➁ Размер товара: {size}\n" \
                           f"➂ Цвет товара: {color}\n" \
                           f"➃ Ссылка на товар: {link}\n" \
                           f"➄ Стоимость товара: {price:.2f}₽ - ({delivery_method})\n" \
                           f"ОБЩАЯ СТОИМОСТЬ: {total_price:.2f}₽\n" \
                           f"Мы выкупаем товар в течение 8 часов после оплаты. Если при выкупе цена изменится, с вами свяжется менеджер для доплаты или возврата средств.\n" \
                           f"Если Вас устраивает, переведите сумму {total_price:.2f}₽ по номеру телефона через:\n" \
                           f"️ Сбербанк или СБП\n" \
                           f"️ 89111684777\n" \
                           f"️ Алексей Александрович В.\n" \
                           f"Осуществляя перевод, вы подтверждаете что корректно указали все данные заказа и согласны со сроками доставки. Мы не несем ответственности за соответствие размеров и брак. После оплаты нажмите кнопку 'Подтвердить оплату'"

    await callback_query.message.answer(confirmation_message, reply_markup=confirmation_keyboard)
    await callback_query.answer()
    unique_order_code = await db.generate_unique_code_for_order()
    state.update_data(unique_order_code=unique_order_code)
    await db.add_order(user.id, category, size, color, link, price, delivery_method, total_price, unique_order_code)


@router.callback_query(F.data == "back_to_cart")
async def back_to_cart(callback_query: CallbackQuery, state: FSMContext, db: Database):
     # Получаем данные пользователя
    user = await db.get_user_by_tg_id(callback_query.from_user.id)
    user_data = {
        'full_name': user.full_name,
        'phone_number': user.phone_number,
        'address': user.main_address
    } 

    # Формируем сообщение для корзины
    data = await state.get_data()
    category = data.get('category', 'Не указано')
    size = data.get('size', 'Не указано')
    color = data.get('color', 'Не указано')
    link = data.get('link', 'Не указано')
    price = data.get('price', 'Не указано')
    delivery_method = data.get('delivery_method', 'Не указано')
    total_price = price * get_currency_cny() #Рассчет стоимости

    cart_message = f"️ КОРЗИНА ЗАКАЗОВ ️\n" \
                   f"ФИО: {user_data['full_name']}\n" \
                   f"Контакт: {user_data['phone_number']}\n" \
                   f"Адрес: {user_data['address']}\n" \
                   f"‍️ ВЫБРАННЫЕ ТОВАРЫ ‍️\n" \
                   f"➀ Категория товара: {category}\n" \
                   f"➁ Размер товара: {size}\n" \
                   f"➂ Цвет товара: {color}\n" \
                   f"➃ Ссылка на товар: {link}\n" \
                   f"➄ Стоимость товара: {price:.2f}₽ - ({delivery_method})\n" \
                   f"ОБЩАЯ СТОИМОСТЬ: {total_price:.2f}₽\n" \

    await callback_query.message.answer(cart_message, reply_markup=cart_keyboard)
    await callback_query.answer()

@router.callback_query(F.data == "confirm_payment")
async def process_confirm_payment(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Подтвердить оплату".
    """
    await callback_query.message.answer("Подтверждение оплаты:\nОтправьте скриншот (фото) произведенной оплаты, чтобы мы убедились, что Вы правильно оплатили заказ")
    await state.set_state(OrderForm.waiting_for_payment_screenshot)
    await callback_query.answer()

@router.message(OrderForm.waiting_for_payment_screenshot, F.photo)
async def process_payment_screenshot(message: Message, state: FSMContext, bot: Bot, db: Database):
    """
    Обработчик получения скриншота оплаты.
    """
    photo = message.photo[-1]  # Берем фото наибольшего разрешения
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    # Здесь можно сохранить файл, отправить его менеджеру и т.д.

# Создаем имя файла для сохранения (можно использовать file_id или message_id)
    file_name = f"payment_{message.from_user.id}_{message.message_id}.jpg"  # Добавляем user_id и message_id
    full_file_path = os.path.join(PAY_SCREENS_DIR, file_name)

   # Создаем имя файла для сохранения (можно использовать file_id или message_id)
    file_name = f"payment_{message.from_user.id}_{message.message_id}.jpg"  # Добавляем user_id и message_id
    full_file_path = os.path.join(PAY_SCREENS_DIR, file_name)

    try:
        # Скачиваем файл и сохраняем его
        await bot.download_file(file_path, full_file_path)

        # Сохраняем путь к файлу в состояние (если нужно)
        await state.update_data(payment_screenshot_path=full_file_path)

        await message.answer("Скриншот оплаты получен и отправлен на проверку.\nОжидайте подтверждения от менеджера.")

        # Отправляем скриншот менеджеру (пример)
        await bot.send_photo(
    chat_id=MANAGER_TELEGRAM_ID,
    photo=FSInputFile(full_file_path),
    caption=f"Новый скриншот оплаты от {message.from_user.full_name} ({message.from_user.id})"
    )
        user = await db.get_user_by_tg_id(message.from_user.id)
        active_orders = await db.get_active_orders_by_tg_id(user.tg_id)
        order = active_orders[-1] #Берем последний заказ, так как он актуальный
        await db.save_payment_screenshot(order.id, full_file_path)

    except Exception as e:
        print(f"Ошибка при сохранении скриншота: {e}")
        await message.answer("Произошла ошибка при сохранении скриншота. Пожалуйста, попробуйте еще раз.")

    finally:
        await state.clear()  # Сбрасываем состояние после завершения обработки



@router.message(OrderForm.waiting_for_payment_screenshot, ~F.photo)
async def process_payment_screenshot_incorrect(message: Message, state: FSMContext):
    """
    Обработчик некорректного ввода (не фото) при ожидании скриншота.
    """
    await message.answer("Пожалуйста, отправьте скриншот (фото) произведенной оплаты.")

@router.callback_query(F.data == "use_promocode")
async def process_use_promocode(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Использовать промокод".
    """
    await callback_query.message.answer("Промокоды: Введите пожалуйста Ваш промокод")
    await state.set_state(OrderForm.waiting_for_promocode)
    await callback_query.answer()

@router.message(OrderForm.waiting_for_promocode)
async def process_promocode(message: Message, state: FSMContext):
    """
    Обработчик ввода промокода.
    Здесь должна быть логика проверки промокода и применения скидки.
    """
    promocode = message.text
    # TODO: Добавить логику проверки промокода и применения скидки
    await message.answer(f"Промокод '{promocode}' принят.\n(Функциональность применения скидки не реализована)")
    await state.clear()  # Сбрасываем состояние

@router.callback_query(F.data == "add_another_item")
async def process_add_another_item(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Добавить товар".
    Возвращает к выбору категории товара.
    """
    await callback_query.message.answer("Выберите категорию товара:\n- От выбора категории зависит стоимость доставки вашего товара",
                                         reply_markup=category_keyboard)
    await state.set_state(OrderForm.waiting_for_category)
    await callback_query.answer()

@router.callback_query(F.data == "remove_items")
async def process_remove_items(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку "Удалить товары".
    TODO: Добавить логику удаления товаров из корзины.
    """
    await callback_query.message.answer("Функциональность удаления товаров из корзины не реализована.")
    await callback_query.answer()

# ===  Отслеживание заказа ===

@router.callback_query(F.data == "track_order")
async def track_order_handler(callback_query: CallbackQuery):
    """
    Обработчик нажатия кнопки "Отследить заказ".
    """
    await callback_query.message.answer(
        "Информация о статусе заказа...",  # Замените на реальную информацию
        reply_markup=track_order_keyboard
    )
    await callback_query.answer()

# === Дополнительные обработчики для кнопок отслеживания ===

@router.callback_query(F.data == "check_status")
async def check_status_handler(callback_query: CallbackQuery):
    """
    Обработчик кнопки "Проверить статус".
    """
    await callback_query.message.answer("Текущий статус вашего заказа: ... (Замените на реальный статус)")
    await callback_query.answer()

@router.callback_query(F.data == "order_history")
async def order_history_handler(callback_query: CallbackQuery):
    """
    Обработчик кнопки "История ваших заказов".
    """
    await callback_query.message.answer("История ваших заказов: ... (Замените на реальную историю)")
    await callback_query.answer()

@router.callback_query(F.data == "status_info")
async def status_info_handler(callback_query: CallbackQuery):
    """
    Обработчик кнопки "Информация о статусах".
    """
    await callback_query.message.answer("Информация о статусах: ... (Замените на реальную информацию)")
    await callback_query.answer()


