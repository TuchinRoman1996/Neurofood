import sqlite3 as sq
from aiogram import types


def sql_start():
    global base, cur
    base = sq.connect('base.db')
    cur = base.cursor()
    base.execute('CREATE TABLE IF NOT EXISTS products('
                 'callback_data,'
                 'name,'
                 'image TEXT,'
                 'description,'
                 'store)'
                 )
    base.execute('CREATE TABLE IF NOT EXISTS client('
                 'client_id,'
                 'product_name,'
                 'count,'
                 'sum)')
    base.execute('CREATE TABLE IF NOT EXISTS properties('
                 'callback_data,'
                 'form,'
                 'weight,'
                 'price)'
                 )
    base.commit()


async def dml(query):
    res = cur.execute(query).fetchall()
    base.commit()
    return res


async def ddl(query):
    res = base.execute(query)
    base.commit()
