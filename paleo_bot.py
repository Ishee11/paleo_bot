import sys
import time
import logging
import datetime
import re
import pickle

#from aiogram.utils import executor
import emoji

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
    person_contact = State()
    name = State()  # Will be represented in storage as 'Form:name'
    phone_number = State()  # Will be represented in storage as 'Form:age'
    check = State()  # Will be represented in storage as 'Form:gender'

bot = Bot(token=cfg.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
msg = []

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
    await bot.set_webhook(cfg.WEBHOOK_URL, max_connections=40, drop_pending_updates=True)

async def on_shutdown(dispatcher):
    await bot.delete_webhook()
    with open('data.pickle', 'wb') as f:
        pickle.dump(start_list, f)

try:
    with open('data.pickle', 'rb') as f:
        start_list = pickle.load(f)
except:
    with open('data.pickle', 'rb') as f:
        # start_list = defaultdict(list) #список: запуск, кнопка запись
        start_list = {} #список: запуск, кнопка запись

async def msg_func(msg, start_list):
    try:
        # start_list_x = list(start_list)
        # print(start_list_x)
        # start_list_y = []
        # print(start_list_y)
        # for i in start_list_x:
        #     start_list_y.append(str('\n'.join(start_list[i][0:])))
        # print(start_list_y)
        print(start_list)
        text_send = {'start': 0, 'pay': 0}
        for i in start_list:
            print(i)
            if start_list[i]['start'] != '':
                text_send['start'] += 1
            if start_list[i]['pay'] != '':
                text_send['pay'] += 1
        print(text_send)
        # text_len = 'Запусков бота: ' + str(len(list(start_list)))
        text_len = 'Запусков бота: ' + str(text_send['start']) + '\nОплат: ' + str(text_send['pay'])
        if msg:
            await bot.edit_message_text(text_len, cfg.admin_chat_id, msg[-1])
        else:
            pass
    except:
        await bot.send_message(cfg.admin_chat_id, text='ошибка')

def get_phone_number():
    markup_request = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
        KeyboardButton(text=emoji.emojize('Отправить свой контакт :telephone:', language='en'), request_contact=True))
    return markup_request

@dp.message_handler(commands=["start"]) #сообщение при старте
async def start_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['msg_id'] = []  # id сообщения о запуске бота
        ikb = InlineKeyboardMarkup(row_width=2)
        ib1 = InlineKeyboardButton(text="Записаться на Палео Марафон", callback_data="booking")
        ikb.add(ib1)
        dt = get_time()
        data['user_username'] = if_none(message.from_user.username)
        # print(data['user_username'])
        data['user_id'] = if_none(message.from_user.id)
        user_full_name = if_none(message.from_user.full_name)
        logging.info(f"{data['user_username']=} {data['user_id']=} {user_full_name=} "+dt)
        # start_list[data['user_id']].append("-> start: ID " + str(data['user_id']) + " @" + str(
        #     data['user_username']) + " " + str(user_full_name) + " " + dt)
        start_list[data['user_id']] = {'start': ("-> start: ID " + str(data['user_id']) + " @" + str(
            data['user_username']) + " " + str(user_full_name) + " " + dt), 'phone': '', 'pay': ''}
        # await msg_func(msg, start_list)
        msg_message = await message.answer(text=emoji.emojize(start.start_message), reply_markup=ikb)
        data['msg_id'] = msg_message['message_id']


@dp.callback_query_handler() #после нажатия кнопки "Записаться..."
async def vote_callback(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['dt'] = get_time()
        data['user_full_name'] = if_none(callback.from_user.full_name)
        if callback.data == "booking":
            data['markup_request'] = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
                KeyboardButton(text=emoji.emojize('Отправить свой контакт :telephone:', language='en'),
                               request_contact=True))
            try:
                await bot.delete_message(callback.from_user.id, data['msg_id'])
            except:
                await bot.send_message(cfg.admin_chat_id, text='ошибка')
            msg_message = await bot.send_message(callback.from_user.id, text=emoji.emojize(
                "При использовании бота необходим Ваш номер телефона.\n"
                "Для согласия нажмите кнопку ниже :down_arrow:\n\n"
                "Если её нет, дважды нажмите кнопку слева от иконки микрофона"),
                                                 reply_markup=data['markup_request'])
            msg_message1 = await bot.send_photo(callback.from_user.id, types.InputFile('button.png'))
            data['msg_id1'] = msg_message['message_id']
            data['msg_id2'] = msg_message1['message_id']
            await Form.person_contact.set()


@dp.message_handler(state=Form.person_contact)
async def contacts(message: types.Message):
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except:
        await bot.send_message(cfg.admin_chat_id, text='ошибка')


@dp.message_handler(content_types=types.ContentType.CONTACT, state=Form.person_contact)
async def contacts(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone_number'] = message.contact.phone_number
        # start_list[data['user_id']].append('-> ' + str(data['phone_number']) + ' ' +
        #                                    data['dt'])
        start_list[data['user_id']]['phone'] = ('-> ' + str(data['phone_number']) + ' ' +
                                           data['dt'])
        # await msg_func(msg, start_list)
        try:
            await bot.delete_message(message.chat.id, data['msg_id1'])
            await bot.delete_message(message.chat.id, data['msg_id2'])
        except:
            await bot.send_message(cfg.admin_chat_id, text='ошибка')
        msg_message = await bot.send_message(message.chat.id, f"Номер успешно получен: {message.contact.phone_number}",
                                             reply_markup=types.ReplyKeyboardRemove())
        data['msg_id'] = msg_message['message_id']
        try:
            await bot.delete_message(message.chat.id, data['msg_id'])
            await bot.delete_message(message.chat.id, message.message_id)
        except:
            await bot.send_message(cfg.admin_chat_id, text='ошибка')
        data['phone_number'] = message.contact.phone_number
        await Form.name.set()
        cancel_kb1 = KeyboardButton('Отменить')
        cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(cancel_kb1)
        await bot.send_message(message.chat.id, 'Представьтесь, пожалуйста!', reply_markup=cancel_kb)


# Выход из процесса регистрации
@dp.message_handler(state='*', commands='Отменить')
@dp.message_handler(Text(equals='Отменить', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
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

    await Form.check.set()
    await bot.send_message(message.from_user.id, emoji.emojize(
                             f"Для участия необходимо внести оплату 3500 руб. по следующим реквизитам:\n\n"
                            f"Сбербанк, номер карты:\n 2202 2011 9759 9042\n"
                             f"или по номеру телефона +79294011192 (Екатерина Евгеньевна С.)\n"
                            f"* в дополнительных полях ничего указывать не нужно.\n\n"
                            f"ОБЯЗАТЕЛЬНО: После оплаты пришлите сюда скриншот перевода :paperclip:\n\n"
                             f"Затем Вы получите ссылку на вступление в канал марафона.", language='en'))


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
            await bot.send_message(cfg.admin_chat_id, text=str(
                data['phone_number']) + '    ' + '@' + data['user_username'])
        elif 'document' in message:
            data['check'] = message.document.file_id
            id_document = data['check']
            await bot.send_document(cfg.admin_chat_id, document=id_document)
            await bot.send_message(cfg.admin_chat_id, text=str(
                data['phone_number']) + '    ' + '@' + data['user_username'])
        else:
            pass

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()

        # And send message
        dt = get_time()
        link1 = await bot.create_chat_invite_link("-1001907992326", member_limit=1)
        ikb = InlineKeyboardMarkup(row_width=2)
        ib1 = InlineKeyboardButton(text="Перейти в канал Палео Марафона", url=str(link1["invite_link"]))
        ikb.add(ib1)
        user_username = if_none(message.from_user.username)
        user_id = if_none(message.from_user.id)
        user_full_name = if_none(message.from_user.full_name)
        logging.info(f"{user_id=} {user_full_name=} {time.asctime()}")
        start_list[user_id]['pay'] = ('-> скрин ' + data['phone_number'] + ' ' + dt)
        qs.main(data['name'], user_id, user_full_name, data['phone_number'], user_username)

        await bot.send_message(message.chat.id, 'Спасибо за оплату!', reply_markup=markup)
        await bot.send_message(message.chat.id, 'Добро пожаловать на Палео Марафон!\n', reply_markup=ikb)

    # Finish conversation
    await state.finish()

@dp.message_handler(commands='runlist')
async def start_list_command(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            msg_message = await bot.send_message(cfg.admin_chat_id, text=message.message_id+1)
            msg.append(msg_message['message_id'])
            await msg_func(msg, start_list)
    except:
        await bot.send_message(cfg.admin_chat_id, text='ошибка')

@dp.message_handler()
async def delete(message: types.Message):
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
# @dp.message_handler()
# async def any_message(message: types.Message):
#     dt = get_time()
#     user_username = if_none(message.from_user.username)
#     user_id = if_none(message.from_user.id)
#     user_full_name = if_none(message.from_user.full_name)
#     goal_user_id = re.findall(r"-?\d+", message.text)
#     if 'help' in message.text:
#         await bot.send_message(cfg.admin_chat_id, text="""
#         Для отправки ссылки введите:\nsend link 'ID'\n\nДля отправки сообщения введите:\nsend message 'ID' 'text message'
#         """)
#     elif 'send link' in message.text:
#         try:
#             link = await bot.create_chat_invite_link("-1001835917627", member_limit=1)
#             ikb = InlineKeyboardMarkup(row_width=2)
#             ib1 = InlineKeyboardButton(text="Перейти в канал Палео Марафона", url=str(link["invite_link"]))
#             ikb.add(ib1)
#             await bot.send_message(goal_user_id[0], text="Ваша ссылка:", reply_markup=ikb)
#         except:
#             await bot.send_message(cfg.admin_chat_id, text='ошибка: некорректный ID')
#     elif 'sm' in message.text:
#         try:
#             message1 = re.findall(r":\s+([^\n]+)", message.text)
#             await bot.send_message(goal_user_id[0], text=''.join(str(message1)[2:-2]))
#         except:
#             await bot.send_message(cfg.admin_chat_id, text='некорректный формат команды\n\nДля отправки сообщения введите:\nsm ID text message')
#     else:
#         await bot.send_message(cfg.admin_chat_id, text=message.text+"\n@" + str(user_username)+" "+str(user_full_name)+ " (ID: "+str(user_id)+")"+"\n"+dt)


# if __name__ == "__main__":
#     executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=cfg.WEBHOOK_PATH,
        skip_updates=False,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=cfg.WEBAPP_HOST,
        port=cfg.WEBAPP_PORT,
    )
