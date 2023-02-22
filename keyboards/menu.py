from data_base import mysql_db as db
from aiogram import types


async def key_home(message):
    basket_client = await db.dml(f'SELECT count(*) FROM orders WHERE user_id = \'{message.from_user.id}\';')
    user = await db.dml(f'SELECT COUNT(*) FROM users WHERE id = \'{message.from_user.id}\';')
    if user[0][0] == 0:
        await db.dml(
            f'INSERT INTO users(`id`, `login`) VALUES ({message.from_user.id}, "{message.from_user.username}");')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ['💲 Каталог', f'️🛒 Корзина ({basket_client[0][0]})']
    keyboard.add(*buttons)
    return keyboard


async def key_phone(message):
    pass