from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from data_base import sqlite_db as db
import re

basket = []


class FSMClient(StatesGroup):
    change_form = State()
    change_weight = State()
    cancel = State()


async def start_command(message: types.Message):
    basket_client = db.dml(f'SELECT sum FROM client WHERE client_id = \'{message.from_user.id}\'')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ['🛒 Каталог', f'🗑️ Корзина ({len(basket_client)})']
    keyboard.add(*buttons)
    await message.answer('Что Вас интересует?', reply_markup=keyboard)


async def catalog_command(message: types.Message):
    products = await db.dml('SELECT name FROM products WHERE remain > 0;')
    buttons = []
    for i in range(len(products)):
        buttons.append(types.InlineKeyboardButton(
            text=products[i][0],
            callback_data=products[i][0]))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await FSMClient.change_form.set()
    await message.answer('Выберите позицию:', reply_markup=keyboard)


async def fn_change_form(callback: types.CallbackQuery, state: FSMContext):
    await FSMClient.change_weight.set()
    product = await db.dml(f'SELECT image, description FROM products WHERE name = \'{callback.data}\'')
    await callback.message.answer_photo(photo=product[0][0], caption=product[0][1])
    forms = await db.dml(f'SELECT form FROM forms WHERE callback_data = \'{callback.data}\' and form != \'0\';')
    buttons = []
    if forms:
        for i in range(len(forms)):
            buttons.append(types.InlineKeyboardButton(
                text=forms[i][0],
                callback_data=forms[i][0]
            ))
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(*buttons)
        await callback.message.answer('Позиция доступна в следующих формах:', reply_markup=keyboard)
    else:
        await fn_change_weight(callback, state)


async def fn_change_weight(callback: types.CallbackQuery, state: FSMContext):
    weight = await db.dml(f'SELECT weight FROM weights WHERE callback_data = \'{callback.data}\'')
    buttons = []
    if weight:
        for i in range(len(weight)):
            buttons.append(types.InlineKeyboardButton(
                text=weight[i][0]+' гр.',
                callback_data=weight[i][0]
            ))
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(*buttons)
        await callback.message.answer('Выберите вес:', reply_markup=keyboard)
    else:
        pass


async def basket_command(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text='✅ Оформить заказ', callback_data='pay'),
        types.InlineKeyboardButton(text='➖ Убрать позицию', callback_data='del')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    answer_text = 'Ваша корзина:\n\n'
    for i in range(len(basket)):
        answer_text += str(i + 1) + '. ' + str(basket[i]) + '\n'
    answer_text += '\n<b>Итого:</b> столько-то рублей.'
    await message.answer(answer_text, reply_markup=keyboard)


async def fn_gid(message: types.Message, state: FSMContext):
    await state.finish()
    if re.search(r'(?i)Каталог', message.text):
        await catalog_command(message)
    if re.search(r'(?i)Корзина', message.text):
        await basket_command(message)
    else:
        basket_client = db.dml(f'SELECT sum FROM client WHERE client_id = \'{message.from_user.id}\'')


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start', 'help'])
    dp.register_message_handler(catalog_command, regexp='(?i)Каталог', state=None)
    dp.register_message_handler(basket_command, regexp='(?i)Корзина')
    dp.register_callback_query_handler(fn_change_form, state=FSMClient.change_form)
    dp.register_message_handler(fn_gid, state='*')
    dp.register_callback_query_handler(fn_change_weight, state=FSMClient.change_weight)
