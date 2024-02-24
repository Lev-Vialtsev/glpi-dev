"""Бот для регистрации"""

import sqlite3
import telebot
from telebot import types

bot_token = '6964646666:AAG1gwMBWXE439pydC54btwBEkuqPK93dDU'
bot = telebot.TeleBot(bot_token)
uname_upass = []
search_id = 0
flag = False


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Проверяем, есть ли id пользователя в базе данных
    if is_user_registered(message, user_id):
        # Пользователь уже зарегистрирован
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_text = "Создать заявку"
        button = types.KeyboardButton(text=button_text)
        markup.add(button)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        # Пользователь не зарегистрирован
        bot.send_message(message.chat.id, "Для начала вам нужно зарегистрироваться. Введите '/register'.")

def is_user_registered(message, user_id):
    global search_id
    conn = sqlite3.connect('D:\Desktop\Yandex_tasks\GLPItelegramBot\database_reg.db')
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM reg_inf WHERE usid = ?', (message.from_user.id,))
    search_id = cur.fetchone()
    
    cur.close()  
    conn.close()
    if search_id:
        return True
    else:
        return False
    

    
@bot.message_handler(commands=['register'])
def register_user(message):
    global search_id
    conn = sqlite3.connect('D:\Desktop\Yandex_tasks\GLPItelegramBot\database_reg.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS
    reg_inf(id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name TEXT, 
    pass TEXT,
    usid INTEGER
    )''')
    conn.commit()
    
    cur.execute('SELECT * FROM reg_inf WHERE usid = ?', (message.from_user.id,))
    search_id = cur.fetchone()
    
    if search_id:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы!')
        
    else:    
        bot.send_message(message.chat.id, 'Введите ваше имя')
        bot.register_next_step_handler(message, name_reg)
        
    cur.execute('SELECT * FROM reg_inf WHERE usid = ?', (message.from_user.id,))
    search_id = cur.fetchone()
    
    cur.close()
    conn.close()
        

def name_reg(message):
    global usname

    usname = message.text.strip()

    bot.send_message(message.chat.id, 'Введите пароль')

    bot.register_next_step_handler(message, pass_reg)


def pass_reg(message):
    global register
    password = message.text.strip()

    conn = sqlite3.connect('D:\Desktop\Yandex_tasks\GLPItelegramBot\database_reg.db')
    cur = conn.cursor()

    cur.execute('INSERT INTO reg_inf(name, pass, usid) VALUES(?, ?, ?)', (usname, password, message.from_user.id))
    conn.commit()
    cur.close()
    conn.close()

    register = True
    bot.send_message(message.chat.id, 'Пользователь успешно зарегистрирован!')    
    

@bot.message_handler(commands=['unregister'])
def start_unregister(message):
    global flag
    bot.send_message(message.chat.id, 'Введите пароль и имя пользователя в формате -> Имя*Пароль')
    flag = True
    bot.register_next_step_handler(message, do_unreg)

@bot.message_handler(func=lambda mes: flag)
def do_unreg(message):
    global uname_upass, flag
    uname_upass = message.text.strip().split('*')
    conn = sqlite3.connect('D:\Desktop\Yandex_tasks\GLPItelegramBot\database_reg.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM reg_inf WHERE name = ? AND pass = ? AND usid = ?', (uname_upass[0], uname_upass[-1], message.from_user.id))
    result = cur.fetchone()

    if result:
        cur.execute('DELETE from reg_inf WHERE name = ? AND pass = ?', (uname_upass[0], uname_upass[-1]))
        conn.commit()
        register = False
        bot.send_message(message.chat.id, 'Вы успешно разрегистрированы!')
        
    elif not result:
        bot.send_message(message.chat.id, 'Пользователь не найден!')
    flag = False
        
    cur.execute('SELECT * FROM reg_inf WHERE usid = ?', (message.from_user.id,))
    search_id = cur.fetchone()
    
    cur.close()
    conn.close()
    
    
    
@bot.message_handler(func=lambda message: message.text == "Создать заявку")
def making_task(message):
    
    bot.send_message(message.chat.id, "Назовите тему заявки!")
    
    bot.register_next_step_handler(message, process_topic)
    

def process_topic(message):
    topic = message.text
    bot.send_message(message.chat.id, "Назовите срочность заявки (от 1 до 10)!")
    bot.register_next_step_handler(message, process_urgency, topic)


def process_urgency(message, topic):
    urgency = message.text
    bot.send_message(message.chat.id, "Назовите глобальность проблемы!")
    bot.register_next_step_handler(message, process_globality, topic, urgency)
    

def process_globality(message, topic, urgency):
    globality = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button1 = types.KeyboardButton(text="описать заново")
    button2 = types.KeyboardButton(text="подтвердить")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, "Вы уверены, что правильно скорректировали заявку?", reply_markup=markup)
    # markup = types.InlineKeyboardMarkup()
    # button1 = types.InlineKeyboardButton(text="описать заново", callback_data="описать_заново")
    # button2 = types.InlineKeyboardButton(text="подтвердить", callback_data="Подтвердить")
    # markup.add(button1, button2)
    # bot.send_message(message.chat.id, "Вы уверены, что правильно скорректировали заявку?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "описать заново")
def again(message):
    
    bot.delete_message(message.chat.id, message.message_id)

    bot.send_message(message.chat.id, 'Для этого нужно выбрать действие "Создать заявку"')


@bot.message_handler(func=lambda message: message.text == "подтвердить")
def accept(message, topic, urgency, globality):
    
    response = f"Проблема: {topic}\nСрочность проблемы: {urgency}\nГлобальность: {globality}"
    bot.send_message(message.chat.id, response)
    bot.send_message(message.chat.id, 'Ваша заявка на рассмотрении!!!')


bot.polling()
