import sys
import time
import logging
import datetime
import re
import pickle

# from aiogram.utils import executor
import emoji

import start
import quickstart as qs
import config as cfg

from aiogram.utils.exceptions import MessageNotModified
from aiogram.utils.executor import start_webhook
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
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
runlist_message = {'message_id': 0}
text_send = {'start': 0, 'pay': 0}


class User:
    def __init__(self, content_types):
        self.user_id = if_none(content_types.from_user.id)
        self.user_username = if_none(content_types.from_user.username)
        self.full_name = if_none(content_types.from_user.full_name)
        self.phone_number = None

    def get_phone(self, content_types):
        self.phone_number = if_none(content_types.contact.phone_number)

    def __str__(self):
        return f'{self.user_id}\n{self.user_username}\n{self.full_name}\n{self.phone_number}'


def get_time():
    delta = datetime.timedelta(hours=10)
    tz = datetime.timezone(delta)
    now = datetime.datetime.now(tz=tz)
    dt = f'{now:%d.%m.%y %H:%M}'
    return dt


def if_none(x):
    return '' if x is None else x


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
        start_list = {}


async def text_send_func(user_id=None, action=None, user_username=None, user_full_name=None, dt=None,
                         phone_number=None):
    try:
        if user_id not in start_list:
            start_list[user_id] = {'start': ("-> start: ID " + str(user_id) + " @" + str(user_username) + " " + str(
                user_full_name) + " " + dt), 'phone': '', 'pay': ''}
            text_send[action] += 1
        if user_id in start_list and start_list[user_id]['pay'] == '' and action == 'pay':
            start_list[user_id]['pay'] = ('-> скрин ' + str(phone_number) + ' ' + str(dt))
            text_send[action] += 1
        print(text_send)
        # print(runlist_message)
    except:
        await bot.send_message(cfg.admin_chat_id, text='ошибка text_send_func')


async def runlist_send(user_id='None', action=None):
    try:
        text_len = 'Запусков бота: ' + str(text_send['start']) + '\nОплат: ' + str(text_send['pay'])
        print(runlist_message)
        if runlist_message['message_id']:
            await bot.edit_message_text(text_len, cfg.admin_chat_id, message_id=runlist_message['message_id'])
        else:
            pass
    except MessageNotModified:
        pass
        # await bot.send_message(cfg.admin_chat_id, text='ошибка runlist_send')


def get_phone_number():
    markup_request = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
        KeyboardButton(text=emoji.emojize('Отправить свой контакт :telephone:', language='en'), request_contact=True))
    return markup_request


@dp.message_handler(commands=["start"]) #сообщение при старте
async def start_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user'] = User(message)
        print(data['user'], sep='__')
        data['msg_id'] = []  # id сообщения о запуске бота
        ikb = InlineKeyboardMarkup(row_width=2)
        ib1 = InlineKeyboardButton(text="Записаться на Палео Марафон", callback_data="booking")
        ikb.add(ib1)
        dt = get_time()
        logging.info(f"{data['user'].user_id} {data['user'].full_name} " + dt)
        await text_send_func(user_id=data['user'].user_id, action='start', user_username=data['user'].user_username,
                             user_full_name=data['user'].full_name, dt=dt)
        msg_message = await message.answer(text=emoji.emojize(start.start_message), reply_markup=ikb)
        data['msg_id'] = msg_message['message_id']
        await runlist_send()


@dp.callback_query_handler()  # после нажатия кнопки "Записаться..."
async def vote_callback(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if callback.data == "booking":
            data['markup_request'] = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
                KeyboardButton(text=emoji.emojize('Отправить свой контакт :telephone:', language='en'),
                               request_contact=True))
            try:
                await bot.delete_message(callback.from_user.id, data['msg_id'])
            except:
                await bot.send_message(cfg.admin_chat_id, text='ошибка удаление сообщения отправка контакта')
            msg_message = await bot.send_message(callback.from_user.id, text=emoji.emojize(
                "При использовании бота необходим Ваш номер телефона.\n"
                "Для согласия нажмите кнопку ниже :down_arrow:\n\n"
                "Если её нет, дважды нажмите кнопку слева от иконки микрофона"),
                                                 reply_markup=data['markup_request'])
            msg_message1 = await bot.send_photo(callback.from_user.id, types.InputFile('button.png'))
            data['msg_id1'] = msg_message['message_id']
            data['msg_id2'] = msg_message1['message_id']
            # await Form.person_contact.set()


# @dp.message_handler(state=Form.person_contact)
@dp.message_handler()
async def contacts(message: types.Message):
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except:
        await bot.send_message(cfg.admin_chat_id, text='ошибка')


@dp.message_handler(content_types=types.ContentType.CONTACT)#, state=Form.person_contact)
async def contacts(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['user']
        except KeyError:
            data['user'] = User(message)
            print(data['user'])
        data['user'].get_phone(message)
        # data['phone_number'] = message.contact.phone_number
        try:
            start_list[data['user'].user_id]['phone'] = ('-> ' + str(data['user'].phone_number) + ' ' + get_time())
        except KeyError:
            pass
        try:
            await bot.delete_message(message.chat.id, data['msg_id1'])
            await bot.delete_message(message.chat.id, data['msg_id2'])
        except:
            await bot.send_message(cfg.admin_chat_id, text='ошибка удаление сообщения после получения контакта')
        msg_message = await bot.send_message(message.chat.id, f"Номер успешно получен: {message.contact.phone_number}",
                                             reply_markup=types.ReplyKeyboardRemove())
        data['msg_id'] = msg_message['message_id']
        try:
            await bot.delete_message(message.chat.id, data['msg_id'])
            await bot.delete_message(message.chat.id, message.message_id)
        except:
            await bot.send_message(cfg.admin_chat_id, text='ошибка удаление сообщения после получения контакта')
        await Form.name.set()
        cancel_kb1 = KeyboardButton('Отменить')
        cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(cancel_kb1)
        await bot.send_message(message.chat.id, 'Представьтесь, пожалуйста!', reply_markup=cancel_kb)


# Выход из процесса регистрации
@dp.message_handler(state='*', commands='Отменить')
@dp.message_handler(Text(equals='Отменить', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info('Cancelling state %r', current_state)
    await state.finish()
    # And remove keyboard (just in case)
    # await callback.message('Cancelled.', reply_markup=types.ReplyKeyboardRemove())
    await message.reply(
        'Регистрация отменена. Для повторного начала регистрации нажмите кнопку "Записаться на Палео Марафон',
        reply_markup=types.ReplyKeyboardRemove())


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
@dp.message_handler(content_types=['photo', 'document'])
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            if 'photo' in message:
                id_doc = message.photo[-1].file_id
                await bot.send_photo(cfg.admin_chat_id, photo=id_doc)
            elif 'document' in message:
                id_doc = message.document.file_id
                await bot.send_document(cfg.admin_chat_id, document=id_doc)
            await bot.send_message(cfg.admin_chat_id, text=str(
                data['user'].phone_number) + '    ' + '@' + data['user'].user_username)
            markup = types.ReplyKeyboardRemove()
            dt = get_time()
            link1 = await bot.create_chat_invite_link("-1001907992326", member_limit=1)
            ikb = InlineKeyboardMarkup(row_width=2)
            ib1 = InlineKeyboardButton(text="Перейти в канал Палео Марафона", url=str(link1["invite_link"]))
            ikb.add(ib1)
            logging.info(f"{data['user'].user_id} {data['user'].full_name} " + dt)
            await text_send_func(user_id=data['user'].user_id, action='pay',
                                 phone_number=data['user'].phone_number, dt=dt)
            qs.main(data['name'], data['user'].user_id, data['user'].full_name, data['user'].phone_number,
                    data['user'].user_username)
            await bot.send_message(message.chat.id, 'Спасибо за оплату!', reply_markup=markup)
            await bot.send_message(message.chat.id, 'Добро пожаловать на Палео Марафон!\n', reply_markup=ikb)
            await runlist_send()
        except KeyError:
            await bot.send_message(message.chat.id, 'Произошла ошибка, пожалуйста, перезапустите бота - /start')
    await state.finish()


@dp.message_handler(commands='runlist')
async def start_list_command(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            message_id = await bot.send_message(cfg.admin_chat_id, text=message.message_id+1)
            runlist_message['message_id'] = message_id['message_id']
            await runlist_send()
    except:
        await bot.send_message(cfg.admin_chat_id, text='ошибка')


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
