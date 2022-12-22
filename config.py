import os

#TOKEN = "1759945997:AAFu2qp0IktDHQnRAjEH-mL2n-qPhe79Ckk" #relaxroom
TOKEN = "5871071094:AAFxcN4mTaEfUlrQ_cRvmdougqygEj05uUI" #paleo
admin_chat_id = "287689713" #ID администратора

# webhook settings
ngrok = 'https://b5ed-95-70-32-149.jp.ngrok.io'
WEBHOOK_HOST = f'https://api.telegram.org/bot5871071094:AAFxcN4mTaEfUlrQ_cRvmdougqygEj05uUI/setwebhook?url= ssh root@'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
# webserver settings
WEBAPP_HOST = '127.0.0.1'
WEBAPP_PORT = os.getenv('4040', default=5000)

#print(WEBHOOK_HOST)