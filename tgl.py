import telebot, requests

bot = None

'''Функции init и connect не прописаны в классе библиотеки, ими является структура основного кода
    и возможность пользователя контактировать с ботом'''

'''Функция init инициализирует телеграмм бота'''

def init(token):
    global bot
    bot = telebot.TeleBot(token)
    return bot

'''Функция send_message принимает на вход чат в который уходит сообщение и тот или иной текст, который оно содержит''' 

def send_message(bot_token, chat_id, message_thread_id, message_text):

    # Формирование URL-адреса
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    # Данные для отправки
    data = {
        'chat_id': chat_id,
        'text': message_text,
        'reply_to_message_id': message_thread_id,  # Указываем ID темы
        'parse_mode': 'HTML'  # Используем HTML
    }

    # Отправка запроса
    response = requests.post(url, data=data)

    # Проверка результата
    if response.status_code == 200:
        print('TGL: Сообщение успешно отправлено!')
    else:
        print('TGL: Ошибка отправки сообщения')

