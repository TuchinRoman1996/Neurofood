from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from data_base import sqlite_db as db
import re


class FSMClient(StatesGroup):

    change_form = State()
    change_weight = State()
    insert_commit = State()
    cancel = State()
    basket = State()
    basket_del = State()


async def start_command(message: types.Message):
    basket_client = await db.dml(f'SELECT count(*) FROM client WHERE client_id = \'{message.chat.username}\'')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ['🛒 Каталог', f'🗑️ Корзина ({basket_client[0][0]})']
    keyboard.add(*buttons)
    if message.text in ['/start', '/help']:
        await message.answer('Добро пожаловать!', reply_markup=keyboard)
    else:
        await message.answer('Корзина обновлена', reply_markup=keyboard)


async def catalog_command(message: types.Message):
    products = await db.dml('SELECT callback_data, name FROM products WHERE store > 0;')
    buttons = []
    for i in range(len(products)):
        buttons.append(types.InlineKeyboardButton(
            text=products[i][1],
            callback_data=products[i][0]))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await FSMClient.change_form.set()
    await message.answer('Выберите позицию:', reply_markup=keyboard)


async def fn_change_form(callback: types.CallbackQuery, state: FSMContext):
    await FSMClient.change_weight.set()
    product = await db.dml(f'SELECT image, description FROM products WHERE callback_data = \'{callback.data}\'')
    await callback.message.answer_photo(photo=product[0][0], caption=product[0][1])
    forms = await db.dml(
        f'SELECT distinct callback_data, form FROM properties WHERE callback_data = \'{callback.data}\' and form != \'-1\';')
    buttons = []
    if forms:
        for i in range(len(forms)):
            buttons.append(types.InlineKeyboardButton(
                text=forms[i][1],
                callback_data=forms[i][0] + '|' + forms[i][1]
            ))
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)
        await callback.message.answer('Позиция доступна в следующих формах:', reply_markup=keyboard)
    else:
        await fn_change_weight(callback, state)


async def fn_change_weight(callback: types.CallbackQuery, state: FSMContext):
    await FSMClient.insert_commit.set()
    if re.search(r'\|', callback.data):
        weight = await db.dml(
            f'SELECT weight, price FROM properties WHERE callback_data = \'{callback.data.split("|")[0]}\''
            f'and form = \'{callback.data.split("|")[1]}\'')
        name = await db.dml(f'SELECT name FROM products WHERE callback_data = \'{callback.data.split("|")[0]}\'')
    else:
        weight = await db.dml(f'SELECT weight, price FROM properties WHERE callback_data = \'{callback.data}\''
                              f'and form = \'-1\'')
        name = await db.dml(f'SELECT name FROM products WHERE callback_data = \'{callback.data}\'')
    buttons = []
    if weight:
        for i in range(len(weight)):
            buttons.append(types.InlineKeyboardButton(
                text=f'{weight[i][0]} гр. = {weight[i][1]} руб.',
                callback_data=f'{name[0][0]}|{weight[i][0]}|{weight[i][1]}'
            ))
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await callback.message.answer('Выберите вес:', reply_markup=keyboard)
    else:
        await final_insert(callback, state)



async def final_insert(callback: types.CallbackQuery, state: FSMContext):
    client_id = callback.from_user.username
    product_name = f'{callback.data.split("|")[0]} - {callback.data.split("|")[1]} гр.'
    count = '1'
    sum = f'{callback.data.split("|")[2]}'
    await db.dml(f'INSERT INTO client(client_id, product_name, count, sum)'
                 f'VALUES (\'{client_id}\', \'{product_name}\', \'{count}\', \'{sum}\')')
    await callback.answer('Добавлен в корзину')
    await callback.message.answer(f'{product_name} добавлен в корзину.')
    await state.finish()
    await start_command(callback.message)


async def basket_command(message: types.Message):
    await start_command(message)
    await FSMClient.basket.set()
    answer_text = 'Ваша корзина пуста'
    basket = await db.dml(f'WITH dc as (SELECT product_name, sum FROM client WHERE client_id = \'{message.from_user.username}\')\n'
                          'SELECT DISTINCT client_id, product_name, sum,\n'
                          '(SELECT count(product_name) FROM dc WHERE dc.product_name = t1.product_name) as count\n'
                          'FROM client t1\n'
                          f'WHERE client_id = \'{message.from_user.username}\'')
    if basket:
        buttons = [
            types.InlineKeyboardButton(text='✅ Оформить заказ', callback_data='pay'),
            types.InlineKeyboardButton(text='➖ Убрать позицию', callback_data='del')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        answer_text = 'Ваша корзина:\n\n'
        control_sum = 0
        for i in range(len(basket)):
            control_sum += int(basket[i][2])
            answer_text += f'{str(i + 1)}. {basket[i][1]}x{basket[i][3]}шт. = {basket[i][2]} руб.\n _______________________\n'
        answer_text += f'\n<b>Итого:</b> {control_sum} руб.'
        await message.answer(answer_text, reply_markup=keyboard)
    else:
        await message.answer(answer_text)
    await message.answer()

async def fn_basket(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'del':
        await FSMClient.basket_del.set()
        await callback.message.answer('Введите номер позици которую хотите удалить:')
    if callback.data == 'pay':
        await callback.message.answer('Подключение кассы в процессе')


async def fn_basket_del(message: types.Message, state: FSMContext):
    basket = await db.dml(f'SELECT DISTINCT product_name FROM client WHERE client_id = \'{message.from_user.username}\'')
    if int(message.text) < 1 or int(message.text)>len(basket) or int(message.text) == -0:
        await message.answer('Нету такой позиции')
    else:
        await db.dml(f'DELETE FROM client WHERE product_name = \'{basket[int(message.text)-1][0]}\'')
        await message.answer(f'Позиция "{basket[int(message.text)-1][0]}" удалена')
        await start_command(message)
        await basket_command(message)
        await state.finish()


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start', 'help'], state='*')
    dp.register_message_handler(catalog_command, regexp='(?i)Каталог', state='*')
    dp.register_message_handler(basket_command, regexp='(?i)Корзин', state='*')
    dp.register_callback_query_handler(fn_change_form,  state=FSMClient.change_form)
    dp.register_callback_query_handler(fn_change_weight, state=FSMClient.change_weight)
    dp.register_callback_query_handler(final_insert, state=FSMClient.insert_commit)
    dp.register_callback_query_handler(fn_basket, state=FSMClient.basket)
    dp.register_message_handler(fn_basket_del, regexp='\d', state=FSMClient.basket_del)
