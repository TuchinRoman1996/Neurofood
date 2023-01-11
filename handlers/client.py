from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from data_base import mysql_db as db
import json


class FSMClient(StatesGroup):
    change_form = State()
    change_weight = State()
    insert_commit = State()
    cancel = State()
    basket = State()
    basket_del = State()


async def updater(message):
    basket_client = await db.dml(f'SELECT count(*) FROM orders WHERE user_id = \'{message.from_user.id}\';')
    user = await db.dml(f'SELECT COUNT(*) FROM users WHERE id = \'{message.from_user.id}\';')
    if user[0][0] == 0:
        await db.dml(
            f'INSERT INTO users(`id`, `login`) VALUES ({message.from_user.id}, "{message.from_user.username}");')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ['💲 Каталог', f'️🛒 Корзина ({basket_client[0][0]})']
    keyboard.add(*buttons)
    return keyboard


async def start_command(message: types.Message):
    keyboard = await updater(message)
    if message.text in ['/start', '/help']:
        await message.answer('Добро пожаловать!', reply_markup=keyboard)
    # else:
    #     await message.answer('Корзина обновлена', reply_markup=keyboard)


async def catalog_command(message: types.Message):
    products = await db.dml('SELECT id, product_name FROM describes;')
    buttons = []
    for i in range(len(products)):
        buttons.append(types.InlineKeyboardButton(
            text=products[i][1],
            callback_data=products[i][0]))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await FSMClient.change_form.set()
    await message.answer('Выберите позицию:', reply_markup=keyboard)


async def fn_change_form(callback: types.CallbackQuery):
    await FSMClient.change_weight.set()
    product = await db.dml(f'SELECT img_address, description FROM describes WHERE id = \'{callback.data}\'')
    await callback.message.answer_photo(photo=product[0][0], caption=product[0][1])
    forms = await db.dml(f'''SELECT DISTINCT f.id, f.form_name 
                                FROM products p
                                JOIN forms f on p.form_id = f.id 
                                WHERE p.describe_id = {callback.data};''')
    buttons = []
    for i in range(len(forms)):
        buttons.append(types.InlineKeyboardButton(
            text=forms[i][1],
            callback_data=json.dumps([callback.data,  # 'describe_id
                                      forms[i][0]  # 'form'
                                      ])
        ))
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    await callback.message.answer('Позиция доступна в следующих формах:', reply_markup=keyboard)


async def fn_change_weight(callback: types.CallbackQuery):
    await FSMClient.insert_commit.set()
    weight = await db.dml(
        f'SELECT weight, price FROM products WHERE describe_id = \'{json.loads(callback.data)[0]}\' '
        f'and form_id = \'{json.loads(callback.data)[1]}\';')
    buttons = []
    json_arr = json.loads(callback.data)
    for i in range(len(weight)):
        b = json_arr + [weight[i][0]]
        buttons.append(types.InlineKeyboardButton(
            text=f'{weight[i][0]} гр. = {weight[i][1]} руб.',
            callback_data=json.dumps(b)
        ))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await callback.message.answer('Выберите вес:', reply_markup=keyboard)


async def final_insert(callback: types.CallbackQuery, state: FSMContext):
    product_id = json.loads(callback.data)[0]
    await db.dml(f'INSERT INTO orders(user_id, product_id, `status`)'
                 f'VALUES (\'{callback.from_user.id}\', \'{product_id}\', \'Ожидает оплаты\')')
    static_keyboard = await updater(callback)
    await callback.message.answer('Товар добавлен в корзину.', reply_markup=static_keyboard)
    await state.finish()


async def basket_command(message: types.Message):
    await start_command(message)
    await FSMClient.basket.set()
    answer_text = 'Ваша корзина пуста'
    basket = await db.dml(f'''
                SELECT o.user_id, 
                d.product_name, 
                f.form_name,
                p.weight,
                COUNT(*),
                sum(p.price)
                FROM orders o 
                JOIN products p on o.product_id = p.id 
                JOIN describes d on p.describe_id = d.id 
                JOIN forms f on p.form_id = f.id
                WHERE o.user_id = {message.from_user.id}
                GROUP BY d.product_name, f.form_name, p.weight;
    ''')
    if basket:
        buttons = [
            types.InlineKeyboardButton(text='✅ Оформить заказ', callback_data='pay'),
            types.InlineKeyboardButton(text='➖ Убрать позицию', callback_data='del')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        answer_text = 'Ваша корзина:\n\n'
        control_sum = await db.dml('SELECT sum(p.price) '
                                   'FROM orders o '
                                   'JOIN products p on o.product_id = p.id '
                                   f'WHERE user_id = {message.from_user.id}')
        for i in range(len(basket)):
            answer_text += f'{str(i + 1)}. {basket[i][1]}({basket[i][2]} {basket[i][3]}гр.)x{basket[i][4]}шт. =' \
                           f' {basket[i][5]} руб.\n'
        answer_text += f'_______________________\n<b>Итого:</b> {control_sum[0][0]} руб.'
        await message.answer(answer_text, reply_markup=keyboard)
    else:
        await message.answer(answer_text)


async def fn_basket(callback: types.CallbackQuery):
    if callback.data == 'del':
        await FSMClient.basket_del.set()
        await callback.message.answer('Введите номер позици которую хотите удалить:')
    if callback.data == 'pay':
        await callback.message.answer('Подключение кассы в процессе')


async def fn_basket_del(message: types.Message, state: FSMContext):
    basket = await db.dml(f'''
                    SELECT 
                    ROW_NUMBER() OVER(ORDER BY o.product_id, f.form_name, p.weight ASC) AS num,
                    o.product_id,
                    sum(p.price)
                    FROM orders o 
                    JOIN products p on o.product_id = p.id 
                    JOIN forms f on p.form_id = f.id
                    WHERE o.user_id = {message.from_user.id}
                    GROUP BY o.product_id, f.form_name, p.weight;
                    ''')
    try:
        if int(message.text) < 1 or int(message.text) > len(basket) or int(message.text) == -0:
            await message.answer('Нету такой позиции')
        else:
            await db.dml(f'''DELETE
                            FROM orders  
                            WHERE product_id in (
                            SELECT product_id FROM(
                            SELECT 
                            ROW_NUMBER() OVER(ORDER BY o.product_id, f.form_name, p.weight ASC) AS num,
                            o.product_id,
                            sum(p.price)
                            FROM orders o 
                            JOIN products p on o.product_id = p.id 
                            JOIN forms f on p.form_id = f.id
                            WHERE o.user_id = {message.from_user.id}
                            GROUP BY o.product_id, f.form_name, p.weight) t1
                            WHERE num = {int(message.text)});''')
            static_keyboard = await updater(message)
            await message.answer(f'Позиция "{basket[int(message.text) - 1][0]}" удалена', reply_markup=static_keyboard)
            await state.finish()

    except ValueError:
        await message.answer('Нужно ввести число')
        await FSMClient.basket_del.set()


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start', 'help'], state='*')
    dp.register_message_handler(catalog_command, regexp='(?i)Каталог', state='*')
    dp.register_message_handler(basket_command, regexp='(?i)Корзин', state='*')
    dp.register_callback_query_handler(fn_change_form, state=FSMClient.change_form)
    dp.register_callback_query_handler(fn_change_weight, state=FSMClient.change_weight)
    dp.register_callback_query_handler(final_insert, state=FSMClient.insert_commit)
    dp.register_callback_query_handler(fn_basket, state=FSMClient.basket)
    dp.register_message_handler(fn_basket_del, state=FSMClient.basket_del)
