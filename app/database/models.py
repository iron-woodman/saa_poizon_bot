import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import MetaData
from sqlalchemy.schema import CreateTable
from sqlalchemy import UniqueConstraint

from app.config import SQLITE_FILE
# --- Конфигурация ---

DATABASE_URL = f"sqlite+aiosqlite:///./{SQLITE_FILE}"  # URL вашей базы данных (sqlite для примера)

# --- Базовая модель ---
Base = declarative_base()

# --- Модели ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    unique_code = Column(String)  # Код для заказов (генерировать при регистрации)
    main_address = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    orders = relationship("Order", back_populates="user") # Связь с таблицей заказов
    def __repr__(self):
        return f"User(id={self.id}, full_name='{self.full_name}', phone_number='{self.phone_number}')"
    

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    order_date = Column(DateTime, default=datetime.datetime.utcnow)
    category = Column(String)
    size = Column(String)
    color = Column(String)
    link = Column(String)
    price = Column(Float)
    delivery_method = Column(String)
    total_price = Column(Float) #Цена с доставкой
    promocode = Column(String, nullable=True)  # Промокод (может быть пустым)
    payment_screenshot = Column(String, nullable=True)  # Путь к скриншоту оплаты (может быть пустым)
    status = Column(String, default="Создан")  # Статус заказа (Создан, Оплачен, В обработке, Отправлен, Завершен, Отменен)
    #Дополнительные поля для отслеживания
    tracking_number = Column(String, nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    order_code = Column(String)

    user = relationship("User", back_populates="orders") # Связь с таблицей пользователей

    def __repr__(self):
        return f"Order(id={self.id}, user_id={self.user_id}, order_date={self.order_date})"
    
    
    
class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True)
    rate_name = Column(String, unique=True)  # e.g., "cny_to_rub"
    rate_value = Column(Float)

    def __repr__(self):
        return f"<ExchangeRate(name='{self.rate_name}', value={self.rate_value})>"
    

class DeliveryPrice(Base):
    __tablename__ = "delivery_prices"

    id = Column(Integer, primary_key=True)
    category = Column(String)
    delivery_type = Column(String)  # 'auto' or 'avia'
    price = Column(Float)

    __table_args__ = (UniqueConstraint('category', 'delivery_type', name='_category_delivery_uc'),)

    def __repr__(self):
        return f"<DeliveryPrice(category='{self.category}', delivery_type='{self.delivery_type}', price={self.price})>"

