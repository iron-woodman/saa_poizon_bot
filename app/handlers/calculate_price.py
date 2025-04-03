import os
from aiogram.fsm.state import State, StatesGroup
from aiogram import types, F, Dispatcher, Bot, Router
from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, FSInputFile, CallbackQuery
from app.keyboards.user_keyboards import main_keyboard


router = Router()


# @router.callback_query(F.data == "calculate_price")
# async def calculate_price(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer(
#         "Пожалуйста, загрузите текстовый файл с принципами (каждый принцип на новой строке).",
#         reply_markup=ReplyKeyboardRemove())
#     await state.set_state(AddQuoteFileState.waiting_for_txtFile)
#     await callback.answer()  #  убрать "кнопка нажата"