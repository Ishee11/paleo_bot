import os

#TOKEN = "1759945997:AAFu2qp0IktDHQnRAjEH-mL2n-qPhe79Ckk" #relaxroom
TOKEN = "5871071094:AAFxcN4mTaEfUlrQ_cRvmdougqygEj05uUI" #paleo
admin_chat_id = "287689713" #ID администратора

# webhook settings
WEBHOOK_HOST = 'https://5100-95-70-91-254.jp.ngrok.io'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=5000)

#HOST_URL = 'https://95.163.235.27'
#WEBHOOK_HOST = f'https://api.telegram.org/bot5871071094:AAFxcN4mTaEfUlrQ_cRvmdougqygEj05uUI/setwebhook?url='+HOST_URL
#95-163-235-27.cloudvps.regruhosting.ru