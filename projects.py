"""Бот для регистрации"""

import sqlite3
import telebot
from telebot import types

bot_token = '6964646666:AAG1gwMBWXE439pydC54btwBEkuqPK93dDU'
bot = telebot.TeleBot(bot_token)

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.is_registered = False
        self.name = None
        self.password = None

    def is_user_registered(self):
        conn = sqlite3.connect('database_reg.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM reg_inf WHERE usid = ?', (self.user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result:
            self.is_registered = True
            self.name = result[1]
            self.password = result[2]
        return self.is_registered

    def register_user(self, name, password):
        conn = sqlite3.connect('database_reg.db')
        cur = conn.cursor()
        cur.execute('INSERT INTO reg_inf(name, pass, usid) VALUES(?, ?, ?)', (name, password, self.user_id))
        conn.commit()
        cur.close()
        conn.close()
        self.is_registered = True
        self.name = name
        self.password = password

    def unregister_user(self):
        conn = sqlite3.connect('database_reg.db')
        cur = conn.cursor()
        cur.execute('DELETE from reg_inf WHERE name = ? AND pass = ? AND usid = ?', (self.name, self.password, self.user_id))
        conn.commit()
        cur.close()
        conn.close()
        self.is_registered = False
        self.name = None
        self.password = None

class Bot:
    def __init__(self, bot_token):
        self.bot = telebot.TeleBot(bot_token)
        self.users = {}
        
    @bot.message_handler(commands=['start'])
    def start(self, message):
        user_id = message.from_user.id
        if user_id not in self.users:
            self.users[user_id] = User(user_id)
        user = self.users[user_id]
        if user.is_user_registered():
            markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            button_text = "Создать заявку"
            button = types.KeyboardButton(text=button_text)
            markup.add(button)
            self.bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        else:
            self.bot.send_message(message.chat.id, "Для начала вам нужно зарегистрироваться. Введите '/register'.")

    @bot.message_handler(commands=['register'])
    def register_user(self, message):
        user_id = message.from_user.id
        user = self.users[user_id]
        if user.is_user_registered():
            self.bot.send_message(message.chat.id, 'Вы уже зарегистрированы!')
        else:
            self.bot.send_message(message.chat.id, 'Введите ваше имя')
            self.bot.register_next_step_handler(message, self.name_reg)

    def name_reg(self, message):
        user_id = message.from_user.id
        user = self.users[user_id]
        user.name = message.text.strip()
        self.bot.send_message(message.chat.id, 'Введите пароль')
        self.bot.register_next_step_handler(message, self.pass_reg)

    def pass_reg(self, message):
        user_id = message.from_user.id
        user = self.users[user_id]
        user.password = message.text.strip()
        user.register_user()
        self.bot.send_message(message.chat.id, 'Пользователь успешно зарегистрирован!')
        
    @bot.message_handler(commands=['unregister'])
    def unregister_user(self, message):
        user_id = message.from_user.id
        user = self.users[user_id]
        if user.is_user_registered():
            self.bot.send_message(message.chat.id, 'Введите пароль и имя пользователя в формате -> Имя*Пароль')
            self.bot.register_next_step_handler(message, self.do_unreg)
        else:
            self.bot.send_message(message.chat.id, 'Вы не зарегистрированы!')

    def do_unreg(self, message):
        user_id = message.from_user.id
        user = self.users[user_id]
        uname_upass = message.text.strip().split('*')
        if user.name == uname_upass[0] and user.password == uname_upass[-1]:
            user.unregister_user()
            self.bot.send_message(message.chat.id, 'Вы успешно разрегистрированы!')
        else:
            self.bot.send_message(message.chat.id, 'Пользователь не найден!')

    def making_task(self, message):
        user_id = message.from_user.id
        user = self.users[user_id]
        if user.is_user_registered():
            if message.text == "Создать заявку":
                self.bot.send_message(message.chat.id, "Назовите тему заявки!")
                self.bot.register_next_step_handler(message, self.process_topic)
        else:
            self.bot.send_message(message.chat.id, 'Вы не зарегистрированы!')

    def process_topic(self, message):
        topic = message.text
        self.bot.send_message(message.chat.id, "Назовите срочность заявки (от 1 до 10)!")
        self.bot.register_next_step_handler(message, self.process_urgency, topic)

    def process_urgency(self, message, topic):
        urgency = message.text
        self.bot.send_message(message.chat.id, "Назовите глобальность проблемы!")
        self.bot.register_next_step_handler(message, self.process_globality, topic, urgency)

    def process_globality(self, message, topic, urgency):
        globality = message.text
        # Сохранение ответов в переменных или базе данных
        # Вывод информации о заявке
        response = f"Проблема: {topic}\nСрочность проблемы: {urgency}\nГлобальность: {globality}"
        self.bot.send_message(message.chat.id, response)
        self.bot.send_message(message.chat.id, 'Ваша заявка на рассмотрении!!!')

    def polling(self):
        self.bot.polling()

bot = Bot(bot_token)
bot.polling()
