import sqlite3

from datetime import datetime
from aiogram import Dispatcher, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message

from cal import calc_events


class Form(StatesGroup):
    url = State()
    filled = State()


async def user_start(message: Message):
    await Form.url.set()
    conn = sqlite3.connect(message.bot['config'].db.name)
    cur = conn.cursor()
    cur.execute(f'SELECT 1 FROM users WHERE user_id = {message.from_user.id}')
    if not cur.fetchone():
        cur.execute(f'INSERT INTO users (user_id) VALUES({message.from_user.id})')
        conn.commit()

    await message.bot.send_message(message.from_user.id, "Введите ссылку на ваш календарь:")


async def user_fill_url(message: Message):
    text = message.text
    if not text.startswith('webcal://'):
        await message.reply('Ссылка должна начинаться с "webcal://"')
    elif not 100 < len(text) < 150:
        await message.reply("Проверьте ссылку, возможно она скопирована неправильно")
    else:
        conn = sqlite3.connect(message.bot['config'].db.name)
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET url = '{text}' WHERE user_id = {message.from_user.id}")
        conn.commit()
        await Form.filled.set()
        await message.reply("Ваш календарь сохранен")


async def user_help(message: Message):
    text = """
<b>Бот работает с публичным календарем icloud. 
Он группирует все события по названию и возвращает статистику по ним.</b>

Для настройки введите команду /start и следуйте инструкциям.
Для получения статистики просто укажите дату, с которой необходимо взять события.

<b>Возможные варианты получения данных:</b>
1) Дата, начиная с которой выбрать события:
<code>1.12.2022</code>
2) Интервал, между которым выбрать события:
<code>1.12.2022 14.12.2022</code>
"""

    await message.bot.send_message(message.from_user.id, text)


async def user_calc(message: Message):
    conn = sqlite3.connect(message.bot['config'].db.name)
    cur = conn.cursor()
    cur.execute(f'SELECT url FROM users WHERE user_id = {message.from_user.id}')
    url = cur.fetchone()
    if not url:
        await message.reply("Вы не заполнили ссылку на календарь. Нажмите /start")
    else:
        url = url[0]
        dates_text = message.text.strip().split()
        if len(dates_text) > 2:
            await message.reply('Можно указать только две даты, разделяя одним пробелом')

        dates = []
        for dt in dates_text:
            try:
                dates.append(datetime.strptime(dt, '%d.%m.%Y'))
            except ValueError:
                await message.reply(f'"{dt}" не похоже на дату в формате ДЕНЬ.МЕСЯЦ.ГОД')

        if len(dates) == 2:
            start_dt = dates[0]
            end_dt = dates[1]
        else:
            start_dt = dates[0]
            end_dt = None

        reply_text = calc_events(url, start_dt, end_dt)

        await message.reply(reply_text)


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_message_handler(user_help, commands=["help"], state="*")
    dp.register_message_handler(user_fill_url, state=Form.url, content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(user_calc, state="*", content_types=types.ContentTypes.TEXT)
