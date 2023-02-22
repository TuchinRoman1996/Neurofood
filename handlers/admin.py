from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from config import super_user
from data_base import mysql_db as db


class FSMAddproduct(StatesGroup):
    check_partner = State()
    user_name = State()
    product_name = State()
    product_desc = State()


async def fn_check_partner(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == '/cancel':
        await callback.message.answer('Действие отменено')
        await state.finish()
    elif callback.data == '/application':
        await callback.message.answer('Введите Ваше ФИО:')
        await FSMAddproduct.user_name.set()


async def fn_user_name(message: types.Message):
    await db.dml(f'UPDATE users SET fullname = "{message.text}" where id = {message.from_user.id};')
    await message.answer('Введите название Вашего товара')
    await FSMAddproduct.product_name.set()


async def fn_product_name(message: types.Message):
    await db.dml(f'''INSERT INTO describes(product_name) VALUES("{message.text[0:99]}");''')
    await db.dml(f'''INSERT INTO applications(user_id, product_id) VALUES ({message.from_user.id},
                      (SELECT id FROM describes WHERE product_name = "{message.text[0:99]}"));''')
    await message.answer('Введите краткое описание Вашего товара:')
    await FSMAddproduct.product_desc.set()


async def fn_product_desc(message: types.Message):
    pass


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
    dp.register_message_handler(dml, commands='dml', state=None)
    dp.register_message_handler(dml_query, state=FSMAdmin.dml_query)
    dp.register_message_handler(cm_start, commands='image', state=None)
    dp.register_message_handler(load_photo, content_types=['photo'], state=FSMAdmin.photo)
    dp.register_message_handler(finish, Text(equals='отмена', ignore_case=True), state='*')
    dp.register_callback_query_handler(fn_check_partner, state=FSMAddproduct.check_partner)
    dp.register_message_handler(fn_user_name, state=FSMAddproduct.user_name)
    dp.register_message_handler(fn_product_name, state=FSMAddproduct.product_name)


