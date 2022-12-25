import time
import logging
import datetime
import re
import pickle

from aiogram.utils import executor

import start
import quickstart as qs
import config as cfg

from aiogram.utils.executor import start_webhook
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    phone_number = State()  # Will be represented in storage as 'Form:age'
    check = State()  # Will be represented in storage as 'Form:gender'

bot = Bot(token=cfg.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
msg = [] #id сообщения о запуске бота

def get_time():
    delta = datetime.timedelta(hours=10)
    tz = datetime.timezone(delta)
    now = datetime.datetime.now(tz=tz)
    dt = now.strftime("%d.%m.%y %H:%M")
    return dt

def if_none(x):
    if x is None:
        x = ''
    return x

async def on_startup(dispatcher):
    await bot.set_webhook(cfg.WEBHOOK_URL, certificate='./fullchain.pem', drop_pending_updates=True)

async def on_shutdown(dispatcher):
    await bot.delete_webhook()
    with open('data.pickle', 'wb') as f:
        pickle.dump(start_list, f)

try:
    with open('data.pickle', 'rb') as f:
        start_list = pickle.load(f)
except:
    with open('data.pickle', 'rb') as f:
        start_list = defaultdict(list) #список: запуск, кнопка запись

async def msg_func(msg, start_list):
    start_list_x = list(start_list)
    start_list_y = []
    for i in start_list_x:
        start_list_y.append(str('\n'.join(start_list[i][0:])))
    text_len = '\n'.join(start_list_y)[0:] + '\n\nЗапусков бота: ' + str(len(list(start_list))) + '\n'
    if msg:
        await bot.edit_message_text(text_len, cfg.admin_chat_id, msg[-1])
    else:
        pass

@dp.message_handler(commands=["start"]) #сообщение при старте
async def start_handler(message: types.Message):
    ikb = InlineKeyboardMarkup(row_width=2)
    ib1 = InlineKeyboardButton(text="Записаться на Палео Марафон", callback_data="enroll")
    ikb.add(ib1)
    dt = get_time()
    user_username = if_none(message.from_user.username)
    user_id = if_none(message.from_user.id)
    user_full_name = if_none(message.from_user.full_name)
    logging.info(f"{user_username=} {user_id=} {user_full_name=} "+dt)
    start_list[user_id].append("Запуск бота: ID: " + str(user_id) + " @" + str(user_username) + " " + str(user_full_name) + " " + dt)
    await msg_func(msg, start_list)
    await message.answer(start.start_message, reply_markup=ikb)

@dp.callback_query_handler() #после нажатия кнопки "Записаться..."
async def vote_callback(callback: types.CallbackQuery):
    dt = get_time()
    user_id = if_none(callback.from_user.id)
    user_full_name = if_none(callback.from_user.full_name)
    if callback.data == "enroll":
        await bot.send_message(callback.from_user.id, f"{user_full_name}, будем рады видеть Вас на нашем Палео Марафоне!\n\nДля участия выполните следующие шаги:\n\n"
                         f"1) напишите Ваши ФИО и номер телефона;\n\n"
                         f"2) внесите оплату 3000 руб. по следующим реквизитам:\n\n"
                        f"Сбербанк, номер карты:\n 2202 2011 9759 9042\n"
                         f"или по номеру телефона +79294011192 (Екатерина Евгеньевна С.)\n"
                        f"* в дополнительных полях ничего указывать не нужно.\n\n"
                        f"3) После оплаты пришлите, пожалуйста, скриншот перевода.\n\n"
                         f"Затем Вы получите ссылку на вступление в канал марафона.")
        start_list[user_id].append('Кнопка "записаться"' + " " + dt)
        await msg_func(msg, start_list)
        await Form.name.set()
        cancel_kb1 = KeyboardButton('Отменить')
        cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(cancel_kb1)
        await bot.send_message(callback.from_user.id, 'Представьтесь, пожалуйста!', reply_markup=cancel_kb)

# Выход из процесса регистрации
@dp.message_handler(state='*', commands='Отменить')
@dp.message_handler(Text(equals='Отменить', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
# async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    """
            Allow user to cancel any action
            """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()

    # And remove keyboard (just in case)
    # await callback.message('Cancelled.', reply_markup=types.ReplyKeyboardRemove())
    await message.reply('Регистрация отменена. Для повторного начала регистрации нажмите кнопку "Записаться на Палео Марафон', reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await Form.next()
    await bot.send_message(message.from_user.id, "Ваш номер телефона")

@dp.message_handler(state=Form.phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(phone_number=str(message.text))
    await bot.send_message(message.from_user.id, "Теперь пришлите скриншот или чек перевода")

@dp.message_handler(lambda message: message.text, state=Form.check)
async def process_check_invalid(message: types.Message):
    return await message.reply("Это не похоже на скриншот или чек об оплате")

@dp.message_handler(content_types=['photo', 'document'], state=Form.check)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if 'photo' in message:
            data['check'] = message.photo[-1].file_id
            id_photo = data['check']
            await bot.send_photo(cfg.admin_chat_id, photo=id_photo)
        elif 'document' in message:
            data['check'] = message.document.file_id
            id_document = data['check']
            await bot.send_document(cfg.admin_chat_id, document=id_document)
        else:
            pass

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()

        # And send message
        dt = get_time()
        link1 = await bot.create_chat_invite_link("-1001835917627", member_limit=1)
        ikb = InlineKeyboardMarkup(row_width=2)
        ib1 = InlineKeyboardButton(text="Перейти в канал Палео Марафона", url=str(link1["invite_link"]))
        ikb.add(ib1)
        user_username = if_none(message.from_user.username)
        user_id = if_none(message.from_user.id)
        user_full_name = if_none(message.from_user.full_name)
        logging.info(f"{user_id=} {user_full_name=} {time.asctime()}")
        start_list[user_id].append('Отправлен скрин/документ"' + " " + dt)
        qs.main(data['name'], user_id, user_full_name, data['phone_number'], user_username)

        await bot.send_message(message.chat.id, 'Спасибо за оплату!', reply_markup=markup)
        await bot.send_message(message.chat.id, 'Добро пожаловать на Палео Марафон!\n', reply_markup=ikb)

    # Finish conversation
    await state.finish()

# @dp.message_handler(content_types=['photo', 'document']) #отвечаем на получение скрина
# async def handle_photo(message: types.Message):
#     dt = get_time()
#     link1 = await bot.create_chat_invite_link("-1001835917627", member_limit=1)
#     ikb = InlineKeyboardMarkup(row_width=2)
#     ib1 = InlineKeyboardButton(text="Перейти в канал Палео Марафона", url=str(link1["invite_link"]))
#     ikb.add(ib1)
#     user_username = if_none(message.from_user.username)
#     user_id = if_none(message.from_user.id)
#     user_full_name = if_none(message.from_user.full_name)
#     logging.info(f"{user_id=} {user_full_name=} {time.asctime()}")
#     start_list[user_id].append('Отправлен скрин/документ"' + " " + dt)
#     if 'photo' in message:
#         id_photo = message.photo[-1].file_id
#         await bot.send_photo(admin_chat_id, photo=id_photo)
#     elif 'document' in message:
#         id_document = message.document.file_id
#         await bot.send_document(admin_chat_id, document=id_document)
#     else:
#         pass
#     await bot.send_message(message.chat.id,
#                            "Спасибо за оплату!\n\nДобро пожаловать на Палео Марафон!\n", reply_markup=ikb)
#     #await bot.send_message(admin_chat_id, text="@" + str(user_username) + " (ID: " + str(user_id) + ")\n" + str(user_full_name) + "\n" + dt)

@dp.message_handler(commands='list')
async def start_list_command(message: types.Message):
    msg_message = await bot.send_message(cfg.admin_chat_id, text=message.message_id+1)
    msg.append(msg_message['message_id'])
    await msg_func(msg, start_list)

@dp.message_handler()
async def any_message(message: types.Message):
    dt = get_time()
    user_username = if_none(message.from_user.username)
    user_id = if_none(message.from_user.id)
    user_full_name = if_none(message.from_user.full_name)
    goal_user_id = re.findall(r"-?\d+", message.text)
    if 'help' in message.text:
        await bot.send_message(cfg.admin_chat_id, text="""
        Для отправки ссылки введите:\nsend link 'ID'\n\nДля отправки сообщения введите:\nsend message 'ID' 'text message'
        """)
    elif 'send link' in message.text:
        try:
            link = await bot.create_chat_invite_link("-1001835917627", member_limit=1)
            ikb = InlineKeyboardMarkup(row_width=2)
            ib1 = InlineKeyboardButton(text="Перейти в канал Палео Марафона", url=str(link["invite_link"]))
            ikb.add(ib1)
            await bot.send_message(goal_user_id[0], text="Ваша ссылка:", reply_markup=ikb)
        except:
            await bot.send_message(cfg.admin_chat_id, text='ошибка: некорректный ID')
    elif 'send message' in message.text:
        try:
            message1 = re.findall(r":\s+([^\n]+)", message.text)
            await bot.send_message(goal_user_id[0], text=''.join(str(message1)[2:-2]))
        except:
            await bot.send_message(cfg.admin_chat_id, text='некорректный формат команды\n\nДля отправки сообщения введите:\nsend message "ID" "text message"')
    else:
        await bot.send_message(cfg.admin_chat_id, text=message.text+"\n@" + str(user_username)+" "+str(user_full_name)+ " (ID: "+str(user_id)+")"+"\n"+dt)


# if __name__ == "__main__":
#     executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=cfg.WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=cfg.WEBAPP_HOST,
        port=cfg.WEBAPP_PORT,
    )
