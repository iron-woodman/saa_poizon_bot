
import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import MetaData, select
from sqlalchemy.schema import CreateTable
import string
import logging  # Импортируем модуль logging
import sqlalchemy
import pandas as pd # Import pandas

from app.database.models import User, Order, Base, DATABASE_URL, ExchangeRate, DeliveryPrice, PaymentDetails  # Добавляем импорт PaymentDetails

# --- Настройка логирования ---
logging.basicConfig(filename="poison_bot.log", level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# --- Асинхронные методы работы с БД ---

class Database:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url)
        self.async_session_maker = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def create_db_and_tables(self):
        try:
            async with self.engine.begin() as conn:
                # await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            logging.error(f"Error creating database and tables: {e}")
            raise

    async def get_async_session(self) -> AsyncSession:
        return self.async_session_maker()

    async def generate_unique_code_for_user(self) -> str:
        """Generates a unique user code in the range A001-Z999."""
        try:
            async with await self.get_async_session() as session:
                query = select(User.unique_code).distinct()
                result = await session.execute(query)
                existing_codes = [row[0] for row in result.all()]

                for letter in string.ascii_uppercase:
                    if letter == 'F': continue
                    for number in range(1, 1000):
                        code = f"{letter}{number:03}"
                        if code not in existing_codes:
                            return code
                return None  # Handle the unlikely case of all codes being exhausted
        except Exception as e:
            logging.error(f"Error generating unique code for order: {e}")
            raise

    async def add_user(self, tg_id: int, full_name: str, phone_number: str, main_address: str, 
                       unique_code: str, telegram_link: str = None): 
        """
        Добавляет нового пользователя в базу данных.

        Args:
            tg_id: Telegram ID пользователя.
            full_name: Полное имя пользователя.
            phone_number: Номер телефона пользователя.
            main_address: Основной адрес пользователя.
            unique_code: Уникальный код пользователя.
            telegram_link: Ссылка на профиль пользователя (опционально).

        Returns:
            User: Объект User, если пользователь успешно добавлен, иначе None.
        """
        try:
            async with await self.get_async_session() as session:
                user = User(
                    tg_id=tg_id,
                    full_name=full_name,
                    phone_number=phone_number,
                    main_address=main_address,
                    unique_code=unique_code,
                    telegram_link=telegram_link
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
        except Exception as e:
            logging.error(f"Error adding user: {e}")
            await session.rollback()
            return None    

    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        try:
            async with await self.get_async_session() as session:
                result = await session.execute(select(User).where(User.phone_number == phone_number))
                user = result.scalars().first()
                return user
        except Exception as e:
            logging.error(f"Error getting user by phone: {e}")
            raise

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        try:
            async with await self.get_async_session() as session:
                user = await session.get(User, user_id)
                return user
        except Exception as e:
            logging.error(f"Error getting user by id: {e}")
            raise

    async def get_user_by_tg_id(self, tg_id: int) -> Optional[User]:
        try:
            async with await self.get_async_session() as session:
                stmt = select(User).where(User.tg_id == tg_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()  # Возвращает один объект User или None
                return user
        except Exception as e:
            logging.error(f"Error getting user by tg_id: {e}")
            return None

    async def add_order(self, user_id: int, category: str, size: str, color: str, link: str,
                        price: float, delivery_method: str, total_price: float, 
                        promocode: Optional[str] = None) -> Order:
        try:
            async with await self.get_async_session() as session:
                order = Order(user_id=user_id, category=category, size=size, color=color, link=link,
                              price=price, delivery_method=delivery_method, total_price=total_price,
                              promocode=promocode)
                session.add(order)
                await session.commit()
                return order
        except Exception as e:
            logging.error(f"Error adding order: {e}")
            raise

    async def get_orders_by_user(self, user_id: int):
        try:
            async with await self.get_async_session() as session:
                result = await session.execute(select(Order).where(Order.user_id == user_id))
                orders = result.scalars().all()
                return orders
        except Exception as e:
            logging.error(f"Error getting orders by user: {e}")
            raise

    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        try:
            async with await self.get_async_session() as session:
                order = await session.get(Order, order_id)
                return order
        except Exception as e:
            logging.error(f"Error getting order by id: {e}")
            raise

    async def get_order_by_code(self, order_code: str) -> Optional[Order]:
        try:
            async with await self.get_async_session() as session:
                result = await session.execute(select(Order).where(Order.id == order_code))
                order = result.scalars().first()
                return order
        except Exception as e:
            logging.error(f"Error getting order by code: {e}")
            raise

    async def get_orders_by_user_code(self, user_code: str) -> Optional[List[Order]]:
        try:
            async with await self.get_async_session() as session:
                stmt = select(Order).join(User, User.id == Order.user_id).where(
                    User.unique_code == user_code).options(joinedload(Order.user))
                result = await session.execute(stmt)
                orders = result.scalars().all()
                return orders
        except Exception as e:
            logging.error(f"Error getting orders by status: {e}")
            raise
   


    async def get_orders_by_status(self, status: str) -> Optional[List[Order]]:
        try:
            async with await self.get_async_session() as session:
                stmt = select(Order).join(User, User.id == Order.user_id).where(Order.status == status).options(joinedload(Order.user))  # Добавляем eager loading
                result = await session.execute(stmt)
                orders = result.scalars().all()
                return orders
        except Exception as e:
            logging.error(f"Error getting orders by status: {e}")
            raise



    async def update_order_status(self, order_code: str, new_status: str):
        try:
            async with await self.get_async_session() as session:

                order = await session.execute(
                    select(Order).where(Order.id == order_code)
                )
                order = order.scalar_one_or_none()

                if order:
                    order.status = new_status
                    await session.commit()
                    return True
                else:
                    return False

        except Exception as e:
            logging.error(f"Error updating order status: {e}")
            if session.in_transaction():  # Проверка, что транзакция активна
                await session.rollback()
            return False

    async def save_payment_screenshot(self, order_id: str, file_path: str):
        try:
            async with await self.get_async_session() as session:
                order = await session.get(Order, order_id)
                if order:
                    order.payment_screenshot = file_path
                    await session.commit()
                else:
                    raise ValueError(f"Order with order_id {order_id} not found")
        except Exception as e:
            logging.error(f"Error saving payment screenshot: {e}")
            raise

    async def update_order_tracking_info(self, order_id: int, tracking_number: str,
                                           estimated_delivery: datetime.datetime):
        try:
            async with await self.get_async_session() as session:
                order = await session.get(Order, order_id)
                if order:
                    order.tracking_number = tracking_number
                    order.estimated_delivery = estimated_delivery
                    await session.commit()
                else:
                    raise ValueError(f"Order with id {order_id} not found")
        except Exception as e:
            logging.error(f"Error updating order tracking info: {e}")
            raise

    async def get_all_orders_by_tg_id(self, tg_id: int) -> List[Order]:
        """
        Извлекает из базы данных все заказы пользователя по его telegram_id.

        Args:
            tg_id: Telegram ID пользователя.

        Returns:
            Список объектов Order, представляющих активные заказы пользователя.
        """
        try:
            async with await self.get_async_session() as session:
                stmt = select(Order).join(User, User.id == Order.user_id).where(User.tg_id == tg_id)
                result = await session.execute(stmt)

            # Возвращаем список объектов Order
            return result.scalars().all()
        except Exception as e:
            logging.error(f"Error getting all orders by tg_id: {e}")
            raise

    async def get_active_orders_by_tg_id(self, tg_id: int) -> List[Order]:
        """
        Извлекает из базы данных все активные заказы пользователя по его telegram_id.

        Args:
            tg_id: Telegram ID пользователя.

        Returns:
            Список объектов Order, представляющих активные заказы пользователя.
        """

        # Определяем список "активных" статусов.  Этот список можно изменить
        # в соответствии с вашей логикой.
        active_statuses = ["Создан", "Оплачен", "В обработке", "Отправлен"]

        # Используем join для объединения таблиц users и orders
        # Фильтруем по tg_id пользователя и статусу заказа
        try:
            async with await self.get_async_session() as session:
                stmt = select(Order).join(User, User.id == Order.user_id).where(User.tg_id == tg_id,
                                                                                   Order.status.in_(active_statuses))
                result = await session.execute(stmt)

            # Возвращаем список объектов Order
            return result.scalars().all()
        except Exception as e:
            logging.error(f"Error getting active orders by tg_id: {e}")
            raise

    # ----------------------------------------------------------
    # Методы для работы с курсом валют и ценами доставки
    # ----------------------------------------------------------

    async def add_or_update_exchange_rate(self, rate_name: str, rate_value: float):
        """Adds or updates an exchange rate in the database."""
        try:
            async with await self.get_async_session() as session:
                # Check if the rate already exists
                existing_rate = await session.execute(
                    select(ExchangeRate).where(ExchangeRate.rate_name == rate_name)
                )
                existing_rate = existing_rate.scalar_one_or_none()

                if existing_rate:
                    # Update existing rate
                    existing_rate.rate_value = rate_value
                else:
                    # Add new rate
                    new_rate = ExchangeRate(rate_name=rate_name, rate_value=rate_value)
                    session.add(new_rate)
                await session.commit()
        except Exception as e:
            logging.error(f"Error adding/updating exchange rate: {e}")
            if session.in_transaction():
                await session.rollback()
            raise

    async def get_exchange_rate(self, rate_name: str) -> Optional[float]:
        """Retrieves an exchange rate from the database by name."""
        try:
            async with await self.get_async_session() as session:
                result = await session.execute(
                    select(ExchangeRate.rate_value).where(ExchangeRate.rate_name == rate_name)
                )
                rate_value = result.scalar_one_or_none()
                return rate_value
        except Exception as e:
            logging.error(f"Error getting exchange rate: {e}")
            raise

    async def add_or_update_delivery_price(self, category: str, delivery_type: str, price: float):
        """Adds or updates a delivery price in the database."""
        try:
            async with await self.get_async_session() as session:
                # Check if the price already exists
                existing_price = await session.execute(
                    select(DeliveryPrice).where(DeliveryPrice.category == category,
                                                DeliveryPrice.delivery_type == delivery_type)
                )
                existing_price = existing_price.scalar_one_or_none()

                if existing_price:
                    # Update existing price
                    existing_price.price = price
                else:
                    # Add new price
                    new_price = DeliveryPrice(category=category, delivery_type=delivery_type, price=price)
                    session.add(new_price)
                await session.commit()
        except Exception as e:
            logging.error(f"Error adding/updating delivery price: {e}")
            if session.in_transaction():
                await session.rollback()
            raise

    async def get_delivery_price(self, category: str, delivery_type: str) -> Optional[float]:
        """Retrieves a delivery price from the database."""
        try:
            async with await self.get_async_session() as session:
                result = await session.execute(
                    select(DeliveryPrice.price).where(DeliveryPrice.category == category,
                                                        DeliveryPrice.delivery_type == delivery_type)
                )
                price = result.scalar_one_or_none()
                return price
        except Exception as e:
            logging.error(f"Error getting delivery price: {e}")
            raise

    # ----------------------------------------------------------
    # Методы для работы с параметрами оплаты
    # ----------------------------------------------------------

    async def add_or_update_payment_details(self, phone_number: str, card_number: str, FIO: str):
        """Adds or updates payment details in the database."""
        try:
            async with await self.get_async_session() as session:
                # Check if payment details already exist
                existing_details = await session.execute(
                    select(PaymentDetails).limit(1)  # Предполагаем, что запись параметров оплаты может быть только одна
                )
                existing_details = existing_details.scalar_one_or_none()

                if existing_details:
                    # Update existing details
                    existing_details.phone_number = phone_number
                    existing_details.card_number = card_number
                    existing_details.FIO = FIO
                else:
                    # Add new details
                    new_details = PaymentDetails(phone_number=phone_number, 
                                                 card_number=card_number, 
                                                 FIO=FIO)
                    session.add(new_details)
                await session.commit()
        except Exception as e:
            logging.error(f"Error adding/updating payment details: {e}")
            if session.in_transaction():
                await session.rollback()
            raise

    async def get_payment_details(self) -> Optional[PaymentDetails]:
        """Retrieves payment details from the database."""
        try:
            async with await self.get_async_session() as session:
                result = await session.execute(
                    select(PaymentDetails).limit(1)  # Предполагаем, что запись параметров оплаты может быть только одна
                )
                payment_details = result.scalar_one_or_none()
                return payment_details
        except Exception as e:
            logging.error(f"Error getting payment details: {e}")
            raise

    async def close(self):
        try:
            await self.engine.dispose()
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")
    # ----------------------------------------------------------
    # Методы для выгрузки данных в Excel (возвращают путь к файлу)
    # ----------------------------------------------------------

    async def export_users_to_excel(self, excel_filename="data/users_report.xlsx") -> Optional[str]:
        """Exports the contents of the 'users' table to an Excel file and returns the file path."""
        try:
            async with await self.get_async_session() as session:
                # Fetch all users from the database
                users = await session.execute(select(User))
                users = users.scalars().all()

                # Convert users to a list of dictionaries
                user_list = [user.__dict__ for user in users]

                # Create a Pandas DataFrame from the list
                df = pd.DataFrame(user_list)

                # Remove unnecessary columns (e.g., '_sa_instance_state')
                df = df = df.drop(columns=['_sa_instance_state'], errors='ignore')

                # Save the DataFrame to an Excel file
                df.to_excel(excel_filename, index=False)

            return excel_filename  # Return the file path
        except Exception as e:
            logging.error(f"Error exporting 'users' table to Excel: {e}")
            return None  # Return None in case of an error

    async def export_orders_to_excel(self, excel_filename="data/orders_report.xlsx") -> Optional[str]:
        """Exports the contents of the 'orders' table to an Excel file and returns the file path."""
        try:
            async with await self.get_async_session() as session:
                # Fetch all orders from the database
                orders = await session.execute(select(Order))
                orders = orders.scalars().all()

                # Convert orders to a list of dictionaries
                order_list = [order.__dict__ for order in orders]

                # Create a Pandas DataFrame from the list
                df = pd.DataFrame(order_list)

                # Remove unnecessary columns (e.g., '_sa_instance_state')
                df = df.drop(columns=['_sa_instance_state'], errors='ignore')

                # Save the DataFrame to an Excel file
                df.to_excel(excel_filename, index=False)

            return excel_filename  # Return the file path
        except Exception as e:
            logging.error(f"Error exporting 'orders' table to Excel: {e}")
            return None  # Return None in case of an error

# --- Пример использования ---

async def main():
    db = Database(DATABASE_URL)
    try:
        await db.create_db_and_tables()

        # Пример добавления пользователя
        user1 = await db.add_user(tg_id = 123123, full_name="Иван Иванов", phone_number="+79991234567", main_address="Москва, ул. Ленина, 1", unique_code="A001")
        print(f"Added user: {user1}")

        # Пример получения пользователя по номеру телефона
        user2 = await db.get_user_by_phone(phone_number="+79991234567")
        print(f"Got user: {user2}")

        # Пример добавления заказа
        order1 = await db.add_order(user_id=user1.id, category="Обувь", size="42", color="Черный", link="https://example.com/shoes", price=100.0,delivery_method="Авто", total_price = 13100.0, order_code="B123")
        print(f"Added order: {order1}")

        # Пример получения заказов пользователя
        orders = await db.get_orders_by_user(user_id=user1.id)
        print(f"User orders: {orders}")

        #Пример получения заказа по ID
        order_test = await db.get_order_by_id(order1.id)
        print(f"Order по ID: {order_test}")

        # Пример добавления и получения параметров оплаты
        await db.add_or_update_payment_details(phone_number="+79001112233", card_number="1234567890123456")
        payment_details = await db.get_payment_details()
        if payment_details:
            print(f"Payment details: Phone: {payment_details.phone_number}, Card: {payment_details.card_number}")
        else:
            print("Payment details not found.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await db.close()




if __name__ == "__main__":
    import asyncio
    from sqlalchemy import select

    asyncio.run(main())
