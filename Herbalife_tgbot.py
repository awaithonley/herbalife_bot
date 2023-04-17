from aiogram import types, executor, Dispatcher, Bot
from sqlite3 import IntegrityError
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3 as sq

#admin id
ADMIN = [803817300, 456179122]

#database commands
def sql_start():
    global base, cur
    base = sq.connect('Herbalife.db')
    cur = base.cursor()
    if base:
        print("Database connected OK")
    base.execute('CREATE TABLE IF NOT EXISTS menu(name TEXT PRIMARY KEY, number TEXT, user_id TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS userid(user_id TEXT PRIMARY KEY)')
    base.execute('CREATE TABLE IF NOT EXISTS ashana(photo TEXT, name TEXT PRIMARY KEY)')
    base.commit()


async def create_profile(user_id):
    user = cur.execute("SELECT 1 FROM userid WHERE user_id == '{key}'".format(key=user_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO userid VALUES(?)", (user_id,))
        base.commit()


async def sql_add_command(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO menu VALUES (?, ?, ?)', tuple(data.values()))
        base.commit()


async def sql_read4(message):
    for ret in cur.execute('SELECT * FROM userid').fetchall():
        await bot.send_message(chat_id=message.from_user.id, text=f"ID: {ret[0]}")


async def sql_add_command2(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO ashana VALUES (?, ?)', tuple(data.values()))
        base.commit()


async def sql_read2(message):
    for ret in cur.execute('SELECT * FROM ashana').fetchall():
        await bot.send_photo(message.from_user.id, ret[0], f"{ret[1]}")


async def sql_read(message):
    for ret in cur.execute('SELECT * FROM menu').fetchall():
        await bot.send_message(chat_id=message.from_user.id, text=f"<b>Продукт: {ret[0]}\nНомер телефона: {ret[1]}</b>", parse_mode='html')


async def edit_profile(state, user_id):
    async with state.proxy() as data:
        try:
            cur.execute("INSERT INTO menu(name, number, user_id) VALUES ('{}', '{}', '{}')".format(
                data['name'], data['number'], user_id))
            base.commit()
            await bot.send_message(chat_id=user_id, text="Ваш заказ создан, ожидайте ответа", reply_markup=mainkb)
        except IntegrityError:
            print(f"кто то пытался отправить сообщение повторно")
            await bot.send_message(chat_id=user_id, text="2 раз нельзя отправлять заказ", reply_markup=mainkb)


async def delete_table1() -> None:
    cur.execute("DELETE FROM menu")

    base.commit()


async def delete_table2() -> None:
    cur.execute("DELETE FROM ashana")

    base.commit()


token = "5756811885:AAEgdTs-pUVs1b7GgFpt7ruUOdgMndf75WU"


storage = MemoryStorage()
bot = Bot(token)
dp = Dispatcher(bot, storage=storage)


admin_kb = ReplyKeyboardMarkup(resize_keyboard=True)
kkaccess = KeyboardButton(text="/Заказы")
kkdellaccess = KeyboardButton(text="/Удалить заказы")
kknews = KeyboardButton(text="3aгрузить⠀меню")
kkdellnews = KeyboardButton(text="/Удалить меню")
kkusersid = KeyboardButton(text="/USERS_ID")
admin_kb.add(kkusersid)
admin_kb.add(kkaccess)
admin_kb.add(kkdellaccess)
admin_kb.add(kknews)
admin_kb.add(kkdellnews)


canckb = ReplyKeyboardMarkup(resize_keyboard=True)
canckb1 = KeyboardButton(text="❌Отменить загрузку")
canckb.add(canckb1)


mainkb = ReplyKeyboardMarkup(resize_keyboard=True)
kb1 = KeyboardButton(text="/menu")
kb2 = KeyboardButton(text="Оформить заказ")
kb3 = KeyboardButton(text="/moderator")
mainkb.insert(kb1)
mainkb.insert(kb2)
mainkb.insert(kb3)


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(f"Здравствуйте , {message.from_user.first_name}, чтобы начать пользоваться ботов можете использовать данные команды ⬇", reply_markup=mainkb)
    await create_profile(user_id=message.from_user.id)


@dp.message_handler(commands=['menu'])
async def cmd_menu(message: types.Message):
    await sql_read2(message)


@dp.message_handler(text=['/Удалить заказы'])
async def cmd_del_menu(message: types.Message):
    if message.from_user.id in ADMIN:
        await delete_table1()
        await message.answer("Таблица успешно удалена")
    else:
        await message.answer("Вы не админ")


@dp.message_handler(text=['/Удалить меню'])
async def cmd_del_menu(message: types.Message):
    if message.from_user.id in ADMIN:
        await delete_table2()
        await message.answer("Таблица успешно удалена")
    else:
        await message.answer("Вы не админ")


class ProfileStateGroup(StatesGroup):
    name = State()
    number = State()


@dp.message_handler(text=['❌Отменить загрузку'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.finish()
    await message.reply('Отменено',
                        reply_markup=mainkb)


@dp.message_handler(text=['Оформить заказ'])
async def cmd_create(message: types.Message):
    await message.reply("Введите\n1.Имя\n2.Номер телефона\nчтобы оформить заказ, но перед этим ознакомьтесь с правилами:\n\nВсе грубые сообщения будут доведены до модераторов, а в случае повторения нарушений вы больше не сможете пользоваться ботом.\n\nЕсли вы 2 раз сделаете заказ то, он не будет отправлен нам(вы можете сделать сразу 2 заказа в 1 сообщений).", reply_markup=canckb)
    await ProfileStateGroup.name.set()


@dp.message_handler(state=ProfileStateGroup.name)
async def load_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply("Отправьте номер телефона")
    await ProfileStateGroup.next()


@dp.message_handler(state=ProfileStateGroup.number)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['number'] = message.text

    await edit_profile(state, user_id=message.from_user.id)
    await state.finish()


@dp.message_handler(commands=['Заказы'])
async def pizza_menu_command(message: types.Message):
    if message.from_user.id in ADMIN:
        await sql_read(message)
    else:
        await message.answer("Вы не админ", reply_markup=mainkb)


#АДМИНКА
@dp.message_handler(commands="USERS_ID")
async def ash_cmd(message: types.Message):
    if message.from_user.id in ADMIN:
        await sql_read4(message)
    else:
        await message.answer("Вы не админ",
                             reply_markup=mainkb)


class ProfileStateGroup2(StatesGroup):
    photo = State()
    name = State()


@dp.message_handler(text=['❌Отменить загрузку'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.finish()
    await message.reply('Отменено',
                        reply_markup=mainkb)


@dp.message_handler(commands=['moderator'])
async def cmd_moderator(message: types.Message):
    if message.from_user.id in ADMIN:
        await bot.send_message(message.from_user.id, 'Доступ выдан',
                               reply_markup=admin_kb)
        await message.delete()
    else:
        await message.answer("Вы не админ")


@dp.message_handler(text=['3aгрузить⠀меню'])
async def cmd_create(message: types.Message):
    if message.from_user.id in ADMIN:
        await message.reply("Отправь фото",
                            reply_markup=canckb)
        await ProfileStateGroup2.photo.set()
    else:
        await message.answer("Вы не админ")


@dp.message_handler(content_types=['photo'], state=ProfileStateGroup2.photo)
async def load_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id

    await message.reply("Отправь описание и цену продукта")
    await ProfileStateGroup2.next()


@dp.message_handler(state=ProfileStateGroup2.name)
async def load_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        await bot.send_photo(chat_id=message.from_user.id, photo=data['photo'], caption=f"{data['name']} смена")

    await sql_add_command2(state)
    await message.reply("Меню загружено",
                        reply_markup=mainkb)
    await state.finish()


async def on_startup(_):
    print("Бот запущен")
    sql_start()


if __name__ == "__main__":
    executor.start_polling(dispatcher=dp, on_startup=on_startup)