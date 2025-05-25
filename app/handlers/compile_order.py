import os
import logging
import datetime
from aiogram import F, Router, Bot, types
from aiogram.types import (Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile)
from aiogram.utils.markdown import hlink
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.config import MANAGER_TELEGRAM_ID, PAY_SCREENS_DIR  # Убедитесь, что у вас настроен MANAGER_TELEGRAM_ID
from app.utils.regex import (normolize_phone_number, validate_international_phone_number_basic,
                                  validate_full_name, 
                                  validate_color, validate_price, validate_link, validate_size)
from app.keyboards.compile_order_kb import (delivery_keyboard, category_keyboard, 
                                                  cart_keyboard, confirmation_keyboard, 
                                                  track_order_keyboard)
from app.keyboards.calculate_order_kb import registration_keyboard
# from app.utils.currency import get_currency_cny
from app.database.database import Database
# Настройка логирования
logging.basicConfig(level=logging.INFO, encoding='utf-8')

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
    cart_items = State() #Состояние для хранения товаров в корзине (список словарей)


# --- Обработчики ---

@router.callback_query(F.data == "assemble_order")
async def start_order_assembly(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """
    Обработчик нажатия на кнопку "Собрать заказ".
    """
    tg_id = callback_query.from_user.id
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
        # Инициализируем список товаров в корзине
        await state.update_data(cart_items=[])
    await callback_query.answer()  # Отвечаем на callback, чтобы убрать часы


@router.callback_query(OrderForm.waiting_for_category, F.data.startswith("category:"))
async def process_category(callback_query: CallbackQuery, state: FSMContext, db: Database):
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

        # Получаем текущий курс юаня к рублю из БД
        cny_to_rub = await db.get_exchange_rate("cny_to_rub")
        if cny_to_rub is None:
            await callback_query.message.answer("Не удалось получить курс юаня из БД.")
            await state.clear()
            await callback_query.answer()
            return None

        text = (
            "Введите сумму товара в CNY:\n\n"
            f"🇨🇳 Курс на сегодня ({datetime.datetime.now().strftime('%d.%m.%Y')}):\n"
            f"👉 ¥1 = {cny_to_rub} ₽\n"
        )

        await callback_query.message.answer(text)
        await state.set_state(OrderForm.waiting_for_price)
        await callback_query.answer()


@router.message(OrderForm.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    """
    Обработчик ввода суммы товара.
    """
    price = await validate_price(message.text)
    if price is None:
        await message.answer("Пожалуйста, введите корректную сумму в формате числа (например, 123.45).  Цена должна быть положительной.")
        return

    await state.update_data(price=price)
    await message.answer(
        '''
📏 Размер товара:\n
Укажите размер Вашего товара, чтобы мы не ошиблись с заказом.\n
Пример: XS или 52 для одежды 👚\n 41 или 37,5 для обуви 👟 . \n
Если товар продается без размера, то напишите слово "НЕТ".
''')
    await state.set_state(OrderForm.waiting_for_size)


@router.message(OrderForm.waiting_for_size)
async def process_size(message: Message, state: FSMContext):
    """
    Обработчик ввода размера товара.
    """
    size = await validate_size(message.text)
    await state.update_data(size=size)
    await message.answer("Введите цвет товара (или напишите слово 'НЕТ') :")
    await state.set_state(OrderForm.waiting_for_color)


@router.message(OrderForm.waiting_for_color)
async def process_color(message: Message, state: FSMContext):
    """
    Обработчик ввода цвета товара.
    """
    color = await validate_color(message.text)
    await state.update_data(color=color)
    await message.answer("Введите ссылку на товар:")
    await state.set_state(OrderForm.waiting_for_link)


@router.message(OrderForm.waiting_for_link)
async def process_link(message: Message, state: FSMContext):
    """
    Обработчик ввода ссылки на товар.
    """
    link = await validate_link(message.text)
    if link is None:
        await message.answer("Пожалуйста, введите корректную ссылку на товар, начинающуюся с http:// или https://.")
        return

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

    # Получаем данные из FSM
    data = await state.get_data()
    category = data.get('category', 'Не указано')
    size = data.get('size', 'Не указано')
    color = data.get('color', 'Не указано')
    link = data.get('link', 'Не указано')
    price = data.get('price', 'Не указано')
    delivery_method = data.get('delivery_method', 'Не указано')

    # Формируем словарь с информацией о товаре
    item = {
        'category': category,
        'size': size,
        'color': color,
        'link': link,
        'price': price,
        'delivery_method': delivery_method
    }

    # Добавляем товар в корзину (в состояние)
    cart_items = data.get('cart_items', [])
    cart_items.append(item)
    await state.update_data(cart_items=cart_items)

    # Отображаем корзину
    await display_cart(callback_query, state, db)


async def display_cart(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """
    Функция для отображения корзины.
    """

    # Получаем данные пользователя
    user = await db.get_user_by_tg_id(callback_query.from_user.id)
    if not user:
        await callback_query.message.answer("Пользователь не найден.")
        return

    user_data = {
        'full_name': user.full_name,
        'phone_number': user.phone_number,
        'address': user.main_address
    }

    # Получаем данные из FSM
    data = await state.get_data()
    cart_items = data.get('cart_items', [])

    # Если корзина пуста
    if not cart_items:
        await callback_query.message.answer("Ваша корзина пуста.")
        return

    # Формируем сообщение для корзины
    cart_message = "️КОРЗИНА ЗАКАЗОВ \n" \
                   f"ФИО: {user_data['full_name']}\n" \
                   f"Контакт: {user_data['phone_number']}\n" \
                   f"Адрес: {user_data['address']}\n" \
                   f"‍ВЫБРАННЫЕ ТОВАРЫ ‍\n"

    total_price_all_items = 0 #Переменная для хранения общей стоимости всех товаров

    # Получаем текущий курс юаня к рублю из БД
    cny_to_rub = await db.get_exchange_rate("cny_to_rub")
    if cny_to_rub is None:
        logging.error("Не удалось получить курс юаня из БД.")
        await callback_query.message.answer("Не удалось получить курс юаня из БД.")
        await state.clear()
        return None

    # Добавляем информацию о каждом товаре
    for i, item in enumerate(cart_items):
        category = item.get('category', 'Не указано')
        size = item.get('size', 'Не указано')
        color = item.get('color', 'Не указано')
        link = item.get('link', 'Не указано')
        price = item.get('price', 'Не указано')
        delivery_method = item.get('delivery_method', 'Не указано')

        # Получаем стоимость доставки для текущего товара
        delivery_price_rub = await db.get_delivery_price(category, delivery_method)
        if delivery_price_rub is None:
           logging.error(f"Не удалось получить цену доставки для категории '{category}' и типа '{delivery_method}' из БД.")
           delivery_price_rub = 0 #Устанавливаем значение по умолчанию
        price_rub = price * float(cny_to_rub)
        total_price = price_rub + delivery_price_rub
        total_price_all_items += total_price #Считаем общую стоимость
        cart_message += f"{i+1}. Категория: {category}, Размер: {size}, Цвет: {color}, Цена: {total_price:.2f}₽\n"

    cart_message += f"ОБЩАЯ СТОИМОСТЬ ВСЕХ ТОВАРОВ: {total_price_all_items:.2f}₽\n"

    # Создаем inline-кнопки для удаления товаров
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Удалить товар", callback_data="remove_items")],
        [InlineKeyboardButton(text="✅ Продолжить оформление", callback_data="continue_checkout")],
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_another_item")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
    ])

    await callback_query.message.answer(cart_message, reply_markup=keyboard)
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

    # Получаем данные из FSM
    data = await state.get_data()
    cart_items = data.get('cart_items', [])

    # Формируем сообщение для подтверждения заказа
    confirmation_message = f"ПОДТВЕРЖДЕНИ ЗАКАЗА\n" \
                        f"ФИО: {user_data['full_name']}\n" \
                        f"Контакт: {user_data['phone_number']}\n" \
                        f"Адрес: {user_data['address']}\n" \
                        f"‍ВЫБРАННЫЕ ТОВАРЫ ‍\n"

    total_price_all_items = 0  # Переменная для хранения общей стоимости всех товаров

    # Получаем текущий курс юаня к рублю из БД
    cny_to_rub = await db.get_exchange_rate("cny_to_rub")
    if cny_to_rub is None:
        logging.error("Не удалось получить курс юаня из БД.")
        await callback_query.message.answer("Не удалось получить курс юаня из БД.")
        await state.clear()
        await callback_query.answer()
        return None

    for i, item in enumerate(cart_items):
        category = item.get('category', 'Не указано')
        size = item.get('size', 'Не указано')
        color = item.get('color', 'Не указано')
        link = item.get('link', 'Не указано')
        price = item.get('price', 'Не указано')
        delivery_method = item.get('delivery_method', 'Не указано')

         # Получаем стоимость доставки в юанях из БД
        delivery_price_rub = await db.get_delivery_price(category, delivery_method)
        if delivery_price_rub is None:
           logging.error(f"Не удалось получить цену доставки для категории '{category}' и типа '{delivery_method}' из БД.")
           delivery_price_rub = 0

        price_rub = price * float(cny_to_rub)
        total_price = price_rub + delivery_price_rub
        total_price_all_items += total_price  # Считаем общую стоимость

        confirmation_message += f"{i+1}. Категория: {category}, Размер: {size}, Цвет: {color}, Цена: {total_price:.2f}₽\n"

    confirmation_message += f"ОБЩАЯ СТОИМОСТЬ ВСЕХ ТОВАРОВ: {total_price_all_items:.2f}₽\n\n"


    payment_details = await db.get_payment_details()

    confirmation_message += (
         f"Мы выкупаем товар в течение 8 часов после оплаты. Если при выкупе цена изменится, с вами свяжется менеджер для доплаты или возврата средств.\n"
        f"Если Вас все устраивает, переведите сумму {total_price_all_items:.2f}₽:\n"
        f"️ Карта (Сбербанк): {payment_details.card_number} \n"
        f"️ или СБП: {payment_details.phone_number}\n"
        f"️ ФИО получателя: {payment_details.FIO}\n\n"
        f"Осуществляя перевод, вы подтверждаете что корректно указали все данные заказа и согласны со сроками доставки. Мы не несем ответственности за соответствие размеров и брак. После оплаты нажмите кнопку 'Подтвердить оплату'"
    )

    await callback_query.message.answer(confirmation_message, reply_markup=confirmation_keyboard)
    await callback_query.answer()
     # Сохраняем информацию о каждом товаре в базе данных
    for item in cart_items:
        category = item.get('category')
        size = item.get('size')
        color = item.get('color')
        link = item.get('link')
        price = item.get('price')
        delivery_method = item.get('delivery_method')

        # Добавляем заказ в базу данных
        await db.add_order(user.id, category, size, color, link, price, delivery_method, total_price)


@router.callback_query(F.data == "back_to_cart")
async def back_to_cart(callback_query: CallbackQuery, state: FSMContext, db: Database):
    await display_cart(callback_query, state, db)  # Используем функцию display_cart

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


        user_id = message.from_user.id
        username = message.from_user.username
        full_name = message.from_user.full_name

        # 1. Ссылка Markdown (лучший вариант)
        user_link_md = hlink(full_name, f"tg://user?id={user_id}")

        # Отправляем скриншот менеджеру (пример)
        await bot.send_photo(
    chat_id=MANAGER_TELEGRAM_ID,
    photo=FSInputFile(full_file_path),
    caption=f"Новый скриншот оплаты от {user_link_md}"
    )
        await message.reply("Информация о вашей оплате отправлена менеджеру.")  #
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
    await message.answer(f"Промокод '{promocode}' не корректный или устарел.")
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
    """
    # Получаем данные из FSM
    data = await state.get_data()
    cart_items = data.get('cart_items', [])

    # Если корзина пуста
    if not cart_items:
        await callback_query.message.answer("Ваша корзина пуста. 😔")
        await callback_query.answer()
        return

   # Создаем клавиатуру с кнопками для удаления каждого товара
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Удалить товар {i+1} ✖️", callback_data=f"remove_item:{i}")]
        for i in range(len(cart_items))
    ])

    await callback_query.message.answer("Выберите товар, который хотите удалить:", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(F.data.startswith("remove_item:"))
async def process_remove_item(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """
    Обработчик нажатия на кнопку "Удалить товар {i}".
    """
    # Получаем индекс товара для удаления
    item_index = int(callback_query.data.split(":")[1])

    # Получаем данные из FSM
    data = await state.get_data()
    cart_items = data.get('cart_items', [])

    # Проверяем, что индекс находится в пределах списка товаров
    if 0 <= item_index < len(cart_items):
        # Удаляем товар из корзины
        del cart_items[item_index]
        await state.update_data(cart_items=cart_items)

        # Отображаем обновленную корзину
        await display_cart(callback_query, state, db)
        await callback_query.answer()

    else:
        await callback_query.answer("Произошла ошибка при удалении товара. 😔")


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
