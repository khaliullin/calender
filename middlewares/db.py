import sqlite3

from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware


class DbMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    def setup(self, manager):
        super().setup(manager)

        conn = sqlite3.connect('calender.db')
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users(user_id INTEGER, url VARCHAR(150))')

    async def pre_process(self, obj, data, *args):
        db_session = obj.bot.get('db')
        # Передаем данные из таблицы в хендлер
        # data['some_model'] = await Model.get()
