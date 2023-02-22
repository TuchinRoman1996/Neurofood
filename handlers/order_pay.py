import re
import typing
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram import types
from data_base import mysql_db as db
from keyboards.menu import key_home


class FSMpay(StatesGroup):
    fullname = State()
    address = State()
    check_info = State()
    aprove_info = State()
    user_edit = State()


async def fn_fullname(msg: typing.Union[types.Contact, types.Message], state: FSMContext):
    contact = msg.contact.phone_number if msg.contact else msg.text
    if msg.text == 'Назад':
        await state.finish()
        # await FSMClient.basket.set()
    elif msg.text == '2':
        pass
    elif not re.search(r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$', contact):
        await FSMpay.fullname.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [types.KeyboardButton(text="Отправить телефон", request_contact=True),
                   types.KeyboardButton(text="Назад")]
        keyboard.add(*buttons)
        await msg.answer('Номер телефона не должен содержать постаронних символов.\n'
                         'Попробуйте снова:', reply_markup=keyboard)
    else:
        await FSMpay.address.set()
        await db.dml(f'UPDATE users SET phone = \'{contact}\' WHERE id = {msg.from_user.id}')
        await msg.answer('Отлично! \nВведите Ваше ФИО:', reply_markup=await key_home(msg))


async def fn_address(message: types.Message):
    check = await db.dml(f'SELECT address FROM users WHERE id = {message.from_user.id}')
    if check[0][0]:
        await db.dml(f'UPDATE users SET fullname = \'{message.text}\' WHERE id = {message.from_user.id}')
        await fn_check_info(message)
    else:
        await FSMpay.check_info.set()
        await db.dml(f'UPDATE users SET fullname = \'{message.text}\' WHERE id = {message.from_user.id}')
        await message.answer('Введите адрес для доставки:')


async def fn_check_info(message: types.Message):
    user_data = await db.dml(f'SELECT fullname, phone, address from users WHERE id = {message.from_user.id}')
    if user_data[0][2]:
        await FSMpay.aprove_info.set()
        buttons = [types.InlineKeyboardButton(text='Все верно ✅', callback_data='aprove'),
                   types.InlineKeyboardButton(text='Изменить ✏️', callback_data='edit')]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await message.answer(f'Проверте правильность введенных данных:\n'
                             f'1. ФИО: {user_data[0][0]}\n'
                             f'2. Телефон: {user_data[0][1]}\n'
                             f'3. Адрес: {user_data[0][2]}', reply_markup=keyboard)
    else:
        await FSMpay.aprove_info.set()
        await db.dml(f'UPDATE users SET address = \'{message.text}\' WHERE id = {message.from_user.id}')
        user_data = await db.dml(f'SELECT fullname, phone, address from users WHERE id = {message.from_user.id}')
        buttons = [types.InlineKeyboardButton(text='Все верно ✅', callback_data='aprove'),
                   types.InlineKeyboardButton(text='Изменить ✏️', callback_data='edit')]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await message.answer(f'Проверте правильность введенных данных:\n'
                             f'1. ФИО: {user_data[0][0]}\n'
                             f'2. Телефон: {user_data[0][1]}\n'
                             f'3. Адрес: {user_data[0][2]}', reply_markup=keyboard)


async def fn_aprove_info(callback: types.CallbackQuery):
    if callback.data == 'aprove':
        await callback.answer('Оплата')
    elif callback.data == 'edit':
        await FSMpay.user_edit.set()
        await callback.message.answer('Введите номер пункта который Вы бы хотели изменить(1|2|3):')


async def fn_user_edit(message: types.Message):
    if message.text == '1':
        await FSMpay.address.set()
        await message.answer('Введите Ваше ФИО заново:')
    elif message.text == '2':
        await FSMpay.fullname.set()
        await message.answer('Введите Ваш номер телефона заново:')
    elif message.text == '3':
        await FSMpay.address.set()
        await message.answer('Введите Ваше адрес заново:')
    else:
        await FSMpay.check_info.set()
        await message.answer('Такого пунта нет')


def register_handlers_order(dp: Dispatcher):
    dp.register_message_handler(fn_fullname, state=FSMpay.fullname, content_types=['contact', 'text'])
    dp.register_message_handler(fn_address, state=FSMpay.address)
    dp.register_message_handler(fn_check_info, state=FSMpay.check_info)
    dp.register_callback_query_handler(fn_aprove_info, state=FSMpay.aprove_info)
    dp.register_message_handler(fn_user_edit, state=FSMpay.user_edit)
