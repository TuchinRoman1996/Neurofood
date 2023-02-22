from aiogram.utils import executor
from create_bot import dp
from handlers import client, admin, order_pay

client.register_handlers_client(dp)
order_pay.register_handlers_order(dp)
admin.register_handlers_admin(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
