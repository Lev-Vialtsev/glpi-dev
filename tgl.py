import telebot, logging, traceback, sys, configparser

bot = None

'''Функции init и connect не прописаны в классе библиотеки, ими является структура основного кода
    и возможность пользователя контактировать с ботом'''

'''Функция init инициализирует телеграмм бота'''

def init(token):
    global bot
    bot = telebot.TeleBot(token)
    return bot

'''Функция send_message принимает на вход чат в который уходит сообщение и тот или иной текст, который оно содержит''' 

def send_message(chat_id, text):
    try:
        bot.send_message(chat_id, text)
    except Exception as e:
        logging.log.error(f"An error occurred while sending a message: {e}")
        traceback.print_exc()
        

