from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
import sqlite3
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import TOKEN

storage = MemoryStorage()

cheks = False 

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

class StateModeAdd(StatesGroup):
    photo = State()
    category = State()
    name = State()
    artikul = State()

class Delete(StatesGroup):
    code = State()

class Search(StatesGroup):
    search_code = State()

#chat_id=-1001859859879 
db = sqlite3.connect('philms.db')
cur = db.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS philms(   
    photo TEXT,
    category TEXT,
    name TEXT,
    code TEXT);
""")    # Создание таблицы

db.commit()

async def start_but(message):
    keyboard = types.ReplyKeyboardMarkup( resize_keyboard=True)
    kod_search = KeyboardButton('Поиск по коду🔎') 
    reklama = KeyboardButton('Написать о рекламе☎️')
    key_admin = KeyboardButton('Админ панель') 
    keyboard.add(kod_search, reklama)
    user_status = await bot.get_chat_member(chat_id='-1001859859879', user_id=message.from_user.id)
    if user_status['status'] == 'administrator':
        keyboard.add(key_admin)
    return keyboard

async def admin_but():
    keyboard_admin = ReplyKeyboardMarkup(resize_keyboard=True)
    key_add = KeyboardButton(text='Добавить код')
    key_delete = KeyboardButton(text='Удалить код')
    key_back = KeyboardButton(text='/start')
    keyboard_admin.add(key_add, key_delete, key_back)
    return keyboard_admin

@dp.message_handler(commands='start') # добавление кнопок и проверка на администратора
async def start(message: types.Message):
    global cheks
    cheks = False
    await message.answer(text='Вас приветствует бот поиска фильмов по коду, с ссылкой на плеер!\nДля удобства работы испульзуйте встроенную клавиатуру.', reply_markup= await start_but(message))

@dp.message_handler(lambda message: 'Админ панель' in message.text)
async def adminka(message: types.Message):
    user_status = await bot.get_chat_member(chat_id='-1001859859879', user_id=message.from_user.id)
    if user_status['status'] == 'administrator':
        await message.answer('Админ панель включена', reply_markup=await admin_but())

@dp.message_handler(lambda message: 'Написать о рекламе☎️' in message.text)
async def reklam(message: types.Message):
    await message.answer('По поводу рекламы писать сюда: https://t.me/Massimo_235')

@dp.message_handler(lambda message: 'Поиск по коду🔎' in message.text, state=None)
async def check_links(message: types.Message):
    user_status = await bot.get_chat_member(chat_id='-1001859859879', user_id=message.from_user.id) 
    if user_status['status'] == 'left':
        inline_kb = InlineKeyboardMarkup(row_width=1)
        url_but1 = InlineKeyboardButton(text='Фильмы', url = 'https://t.me/filmiztikt')
        check_links = InlineKeyboardButton(text='Проверить подписку✅', callback_data='check')
        inline_kb.add(url_but1, check_links)
        await message.answer('Для начала подпишитесь на эти каналы-спонсоры, чтобы узнать название. Затем нажмите на кнопку «Проверить подписку✅»', reply_markup=inline_kb)
    else:
        await message.answer('Введите код фильма')
        await Search.search_code.set()

@dp.message_handler(state=Search.search_code)
async def searching(message: types.Message, state=FSMContext):
    try:
        cur.execute(f'SELECT * FROM philms WHERE code ={message.text}')
        data = cur.fetchone()
        await message.answer_photo(photo=data[0],caption=f'Категория: {data[1]}\nНазвание: {data[2]}')
        await state.finish()
    except:
        await message.answer('Извините, такого кода не существует!\nПожауйста, повторите попытку.')
        await state.finish()
        
@dp.callback_query_handler(lambda c: c.data == 'check')
async def checking(message: types.CallbackQuery):
    global cheks
    user_status = await bot.get_chat_member(chat_id='-1001859859879', user_id=message.from_user.id) 
    if user_status['status'] == 'left':
        cheks = False
        await bot.answer_callback_query(message.id, text='Вы не подписаны на канал❌', show_alert=True)
    else:
        cheks = True
        await bot.answer_callback_query(message.id, text='Good luck!', show_alert=True)

@dp.message_handler(lambda message: 'Удалить код' in message.text, state=None)
async def delete(message: types.Message):
    user_status = await bot.get_chat_member(chat_id='-1001859859879', user_id=message.from_user.id)
    if user_status['status'] == 'administrator':
        await Delete.code.set()
        await message.answer('Введите артикул для удаления')
    else:
        await message.answer('У вас нет доступа к этой комманде!')
        return
    
@dp.message_handler(state=Delete.code) # удаление кода из бд
async def delete_code(message: types.Message, state=FSMContext):
        try:
            cur.execute(f'DELETE FROM philms WHERE code = {message.text}')
            db.commit()
            await message.answer(f'Код {message.text} успешно удален!', reply_markup= await start_but(message))
        except:
            await message.answer('Ошибка! Такого кода нет в таблице.')
        await state.finish()
#Запуск состояния машины
@dp.message_handler(lambda message: 'Добавить код' in message.text, state=None)
async def state_start(message: types.Message):
    user_status = await bot.get_chat_member(chat_id='-1001859859879', user_id=message.from_user.id)
    if user_status['status'] == 'administrator':
        await StateModeAdd.photo.set()
        await message.answer('Загрузить фото')
    else:
        await message.answer('У вас нет доступа к этой комманде!')
        return
#ловим первый ответ состояния
@dp.message_handler(content_types=['photo'], state=StateModeAdd.photo)
async def load_photo(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id #Добавление в словарь
        print(message.photo)
    cat_murkup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    but_film = KeyboardButton('Фильмы')
    but_serial = KeyboardButton('Сериалы')
    but_anime = KeyboardButton('Аниме')
    cat_murkup.add(but_film, but_serial, but_anime)
    await StateModeAdd.next()
    await message.answer('Введи категорию', reply_markup=cat_murkup) 

# Ловим второй ответ
@dp.message_handler(state=StateModeAdd.category)
async def save_ctg(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['category'] = message.text
        #ReplyKeyboardRemove()
    await StateModeAdd.next()
    await message.answer('Введи название')

# Ловим третий ответ
@dp.message_handler(state=StateModeAdd.name)
async def save_name(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await StateModeAdd.next()
    await message.answer('Введи артикул')

#Ловим последний ответ
@dp.message_handler(state=StateModeAdd.artikul)
async def save_artic(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['artikul'] = message.text
    async with state.proxy() as data:
        cur.execute('INSERT INTO philms VALUES (?,?,?,?);',(data['photo'], data['category'], data['name'], data['artikul']))
        db.commit()
    await state.finish()
    await message.answer('Код добавлен!',reply_markup= await start_but(message))

@dp.message_handler(state="*", commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def close_state(message: types.Message, state=FSMContext):
    current_state = await state.get_state()
    print(await state.get_state())
    if current_state is None:
        return
    await state.finish()
    await message.answer('OK', reply_markup= await start_but(message))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)