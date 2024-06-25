import telebot, json, requests, logging, traceback, configparser

bot_token = '6964646666:AAG1gwMBWXE439pydC54btwBEkuqPK93dDU'
bot = telebot.TeleBot(bot_token)

class LibraryTelegram():
    # Функции init и connect не прописаны в классе библиотеки, 
    # ими является структура основного кода и возможность в пользователя контактировать с ботом.
    def send_message(message, place, text):
        bot.send_message(message.place, text)
    
    def 