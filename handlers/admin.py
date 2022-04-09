from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import super_user
from data_base import sqlite_db

class FSMAdmin(StatesGroup):
    photo = State()
    name = State()
    description = State()
    price = State()



async def cm_start(message: types.Message):
    if message.from_user.username == super_user:
        await FSMAdmin.photo.set()
        await message.reply('Загрузи фото')


async def load_photo(message: types.Message, state: FSMContext):
    if message.from_user.username == super_user:
        async with state.proxy() as data:
            data['photo'] = message.photo[0].file_id
        await FSMAdmin.next()
        await message.reply(str(message.photo[0].file_id))



def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(cm_start, commands='Загрузить', state=None)
    dp.register_message_handler(load_photo, content_types=['photo'], state=FSMAdmin.photo)

