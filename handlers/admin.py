from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from config import super_user
from data_base import sqlite_db as db


class FSMAdmin(StatesGroup):
    photo = State()
    ddl = State()
    ddl_query = State()
    dml = State()
    dml_query = State()
    finish = State()


async def dml(message: types.Message):
    if message.from_user.username == super_user:
        await FSMAdmin.dml_query.set()
        await message.reply('Введите запрос')


async def dml_query(message: types.Message, state: FSMContext):

    res = await db.dml(message.text)
    await message.reply(str(res))
    await state.finish()


async def ddl(message: types.Message):
    if message.from_user.username == super_user:
        await FSMAdmin.ddl_query.set()
        await message.reply('Введите запрос')


async def ddl_query(message: types.Message, state: FSMContext):
    res = await db.ddl(message.text)
    await message.reply(str(res))
    await state.finish()


async def cm_start(message: types.Message):
    if message.from_user.username == super_user:
        await FSMAdmin.photo.set()
        await message.reply('Загрузи фото')


async def load_photo(message: types.Message, state: FSMContext):
    if message.from_user.username == super_user:
        async with state.proxy() as data:
            data['photo'] = message.photo[0].file_id
    await message.reply(str(message.photo[0].file_id))
    await state.finish()


async def finish(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('OK')


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(ddl, commands='ddl', state=None)
    dp.register_message_handler(ddl_query, state=FSMAdmin.ddl_query)
    dp.register_message_handler(dml, commands='dml', state=None)
    dp.register_message_handler(dml_query, state=FSMAdmin.dml_query)
    dp.register_message_handler(cm_start, commands='image', state=None)
    dp.register_message_handler(load_photo, content_types=['photo'], state=FSMAdmin.photo)
    dp.register_message_handler(finish, Text(equals='отмена', ignore_case=True), state='*')

