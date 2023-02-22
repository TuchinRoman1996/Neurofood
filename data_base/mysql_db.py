from config import user, password
from mysql.connector import connect, Error

try:

    connection = connect(
        host="localhost",
        user=user,
        password=password
    )
    cursor = connection.cursor()
    cursor.execute('USE neurofood;')


    async def dml(query):
        cursor.execute(query)
        res = cursor.fetchall()
        connection.commit()
        return res

except Error as e:
    print(e)
