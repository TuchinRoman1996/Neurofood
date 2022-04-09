import sqlite3 as sq
from aiogram import types


def sql_start():
    global base, cur
    base = sq.connect('base_sql.db')
    cur = base.cursor()
    base.execute('CREATE TABLE IF NOT EXISTS products('
                 'image TEXT, '
                 'name PRIMARY_KEY,'
                 'description, '
                 'remain INTEGER)'
                 )
    base.execute('CREATE TABLE IF NOT EXISTS forms('
                 'callback_data, '
                 'form, '
                 'rate)'
                 )
    base.execute('CREATE TABLE IF NOT EXISTS weights('
                 'callback_data, '
                 'weight,'
                 'rate)'
                 )
    base.execute('CREATE TABLE IF NOT EXISTS client('
                 'client_id,'
                 'product,'
                 'form,'
                 'weight,'
                 'count,'
                 'sum)')
    base.commit()


async def dml(query):
    res = cur.execute(query).fetchall()
    return res


async def ddl(query):
    res = base.cursor(query)
    base.commit()
