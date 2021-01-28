import aiogram
import asyncio
import sys, os
import emoji
import datetime
import bitlyshortener
import aioschedule
import sqlite3

from google.cloud import storage as google
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from promocode import codes
from sql import Sqlite




credential_path = r""
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
storage_client = google.Client()
bucket = storage_client.get_bucket("")

API_TOKEN = ""

db = Sqlite(r'')

storage=MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)


tokens_pool = ['']
shortener = bitlyshortener.Shortener(tokens=tokens_pool, max_cache_size=256)

class fsm(StatesGroup):
    start = State()
    perehod = State()
    group = State()
    raspisanie = State()
    semestr = State()
    subject = State()
    folder = State()
    file = State()
    youtube = State()


@dp.message_handler(state="*", commands=["showlogs"])
async def logs(message : types.Message):
    bitly = shortener.usage()
    users = len(db.get_users())
    files = len(db.get_files())
    await bot.send_message(message.chat.id,
        f'Shortener - {bitly}\n'
        f'Пользователей - {users}\n'
        f'Файлов выдано - {files}'
        )

@dp.message_handler(state="*", commands=["start"])
@dp.message_handler(
    lambda message: (message.text.lower() == "start")
    or (message.text.lower() == "старт"),
    state="*",
)
async def say_start(message : types.Message):
    but1 = KeyboardButton("Кладбище файлов")
    but2 = KeyboardButton("Help/errors")
    but3 = KeyboardButton("Donate me a coffee " + emoji.emojize(':coffee:', use_aliases=True))
    kb = ReplyKeyboardMarkup()
    kb.add(but1)
    kb.add(but2, but3)
    await fsm.perehod.set()
    await bot.send_message(
        message.chat.id,
        f"\n"
        f"        Бонжур, {message.from_user.full_name} !\n"
        f"Именем меня не наградили, но я все равно могу помочь.\n"
        f"Я надеюсь, что ты найдешь здесь что-то полезное.\n",
        reply_markup=kb,
    )
    if db.user_exists(message.from_user.id):
        pass
    else:
        db.add_new(
            message.from_user.id,
            message.from_user.full_name,
            message.from_user.username,
            datetime.datetime.now())


@dp.message_handler(state="*", text = codes)
async def count(message : types.Message):
    db.get_promo(True, message.from_user.id)
    await bot.send_message(message.chat.id, 'Вы ввели код %s' % message.text)


@dp.message_handler(state="*", commands=["cancel"])
@dp.message_handler(
    lambda message: (message.text.lower() == "отмена")
    or (message.text.lower() == "cancel")
    or (message.text.lower() == "назад"),
    state="*",
)
async def cancel_handler(message: types.Message, state: fsm):
    await state.reset_state()
    await bot.send_message(
        message.chat.id,
        """До новых встреч!
Возобновить работу /start""",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@dp.message_handler(state=fsm.perehod)
async def perehod(message : types.Message):
    if message.text == "Кладбище файлов":
        await fsm.semestr.set()
        but1 = KeyboardButton("1 Семестр")
        but2 = KeyboardButton("2 Семестр")
        but3 = KeyboardButton("3 Семестр")
        but4 = KeyboardButton("4 Семестр")
        but5 = KeyboardButton("5 Семестр")
        but6 = KeyboardButton("6 Семестр")
        but7 = KeyboardButton("Циклы")
        but_cancel = KeyboardButton("Отмена")
        kb = ReplyKeyboardMarkup()
        kb.add(but1, but2)
        kb.add(but3, but4)
        kb.add(but5, but6)
        kb.add(but7)
        kb.add(but_cancel)
        await bot.send_message(message.chat.id, "Выберите необходимое", reply_markup=kb)
    elif message.text == "Help/errors":
        await bot.send_message(
            message.chat.id,
            """""",
        )
    elif message.text == ("Donate me a coffee " + emoji.emojize(':coffee:', use_aliases=True)):
        await bot.send_message(
            message.chat.id,
            "https://money",
        )


@dp.message_handler(state=fsm.semestr)
async def predmet(message : types.Message):
    if 'Семестр' in message.text:
        a = []
        sem = message.text[0:1] + "sem"
        db.update_info('semestr', sem, message.from_user.id)
        blobs = bucket.list_blobs(prefix=sem)
        keyb = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
        for blob in blobs:
            blob.name = str(blob.name)[5:]
            splitted = blob.name.split("/")
            splitted = splitted[0]
            if splitted not in a:
                a.append(splitted)
                button = KeyboardButton(splitted)
                keyb.add(button)
        keyb.add(KeyboardButton("Отмена"))
    else:
        a = []
        db.update_info('semestr', message.text, message.from_user.id)
        blobs = bucket.list_blobs(prefix=db.select_one(message.from_user.id, 8))
        keyb = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
        for blob in blobs:
            blob.name = str(blob.name)[6:]
            splitted = blob.name.split("/")
            splitted = splitted[0]
            if splitted not in a:
                a.append(splitted)
                button = KeyboardButton(splitted)
                keyb.add(button)
        keyb.add(KeyboardButton("Отмена"))
    await fsm.subject.set()
    await bot.send_message(message.chat.id, "Выберите предмет", reply_markup=keyb, )

@dp.message_handler(state=fsm.subject)
async def predmet(message : types.Message):
    a = []
    db.update_info('subject', message.text, message.from_user.id)
    blobs = bucket.list_blobs(prefix=db.select_one(message.from_user.id, 8) + "/" + db.select_one(message.from_user.id, 9))
    keyb = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
    for blob in blobs:
        sep = "/"
        splitted = blob.name.split(sep)
        splitted = splitted[2]
        if splitted not in a:
            a.append(splitted)
            button = KeyboardButton(splitted)
            keyb.add(button)
    keyb.add(KeyboardButton("Отмена"))
    await fsm.folder.set()
    await bot.send_message(message.chat.id, 'Выберите категорию', reply_markup=keyb)


@dp.message_handler(state=fsm.folder)
async def papka(message : types.Message):
    a = []
    db.update_info('folder', message.text, message.from_user.id)
    blobs = bucket.list_blobs(prefix = db.select_one(message.from_user.id, 8) + "/" + db.select_one(message.from_user.id, 9) + '/' + db.select_one(message.from_user.id, 10))
    keyb = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
    for blob in blobs:
            sep = "/"
            splitted = blob.name.split(sep)
            splitted = splitted[3]
            if splitted not in a:
                a.append(splitted)
                if message.text == 'Видео':
                    splitted = splitted[:-4]
                    await fsm.youtube.set()
                else:
                    await fsm.file.set()
                button = KeyboardButton(splitted)
                keyb.add(button)
    keyb.add(KeyboardButton('Отмена'))
    await bot.send_message(message.chat.id, 'Выберите файл ', reply_markup=keyb)

@dp.message_handler(state=fsm.file)
async def file(message : types.Message):
    if db.select_one(message.from_user.id, 4) < 5:
        if not db.select_one(message.from_user.id, 6):
            count = db.select_one(message.from_user.id, 4)
            count +=1
            db.update_info('count', count, message.from_user.id)
            await bot.send_message(message.chat.id, 'Скачано файлов - %i из 5' % count)
        db.update_info('file', message.text, message.from_user.id)
        info = db.select_one(message.from_user.id, 8) + "/" + db.select_one(message.from_user.id, 9) + '/' + db.select_one(message.from_user.id, 10) + "/" + db.select_one(message.from_user.id, 11)
        link = (
            ""
            + info
        )
        linken = [link]
        short_link = shortener.shorten_urls(linken)[0]
        await bot.send_message(
            message.chat.id,
            "%s"
            % short_link,
        )
        await bot.send_message(message.chat.id, 'Продолжить работу с ботом /start')

        all_files_count = db.select_one(message.from_user.id, 3)
        all_files_count += 1
        db.update_info('all_files', all_files_count, message.from_user.id)
        db.file_insert(message.from_user.id, info, datetime.datetime.now())
        return
    else:
        await bot.send_message(message.chat.id, 'Вы исчерпали лимит скачиваний на сегодня, возвращайтесь завтра!')


@dp.message_handler(state=fsm.youtube)
async def video(message : types.Message):
    link = 'bit.do/' + message.text
    await bot.send_message(message.chat.id, link)
    await bot.send_message(message.chat.id, 'Продолжить работу с ботом /start')
    video = db.select_one(message.from_user.id, 8) + "/" + db.select_one(message.from_user.id, 9) + ' | ' + message.text
    db.file_insert(message.from_user.id, video, datetime.datetime.now())

async def zeroing():
    db.zeroing()

async def scheduler():
    aioschedule.every().day.at("00:00").do(zeroing)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(x):
    asyncio.create_task(scheduler())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

