from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMOrder (StatesGroup):
    order_full_name = State()
    order_address = State()


async def client_data(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите ФИО:')

def register_handlers_order(dp: Dispatcher):
    dp.register_callback_query_handler(client_data, State = FSMOrder.order_phone)


