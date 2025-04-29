# app/middlewares/database.py
from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from app.database.database import Database


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db

    async def __call__(
        self,
        handler: Callable[[CallbackQuery | Message, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: dict[str, Any]
    ) -> Any:
        data["db"] = self.db  # Добавляем db в data
        return await handler(event, data)
