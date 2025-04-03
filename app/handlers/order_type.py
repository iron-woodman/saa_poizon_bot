from aiogram.fsm.state import State, StatesGroup
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, CallbackQuery
from app.keyboards.user_keyboards import main_keyboard, order_type_keyboard


router = Router()

# FSM States
class AddQuoteState(StatesGroup):
    waiting_for_quote = State()


@router.callback_query(lambda c: c.data == 'retail')
async def process_callback_retail(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("Вы выбрали розничный расчет!")

@router.callback_query(lambda c: c.data == 'wholesale')
async def process_callback_wholesale(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("Вы выбрали оптовый расчет!")

# @router.callback_query(lambda c: c.data == 'main_menu')
# async def process_callback_main_menu(callback_query: types.CallbackQuery):
#     await callback_query.answer()
#     await callback_query.message.answer("Возврат в главное меню...")




# @router.message(AddQuoteState.waiting_for_quote, F.text)
# async def process_quote(message: types.Message, state: FSMContext):
#     quote = message.text.strip()
#     if quote:
#         quotes.add_quote(message.from_user.id, quote)
#         await message.reply("Ваш новый принцип добавлен!", reply_markup=main_keyboard)
#         # else:
#         #     await message.reply("Произошла ошибка при добавлении нового принципа.", reply_markup=main_keyboard)
#         await state.clear()
#
#     else:
#         await message.answer("Пожалуйста, укажите принцип для добавления.")


@router.callback_query(F.data == "calculate_price")
async def define_order_type(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Для рассчета стоимости выбирите тип заказа", reply_markup=order_type_keyboard)
    await callback.answer()  #  убрать "кнопка нажата"