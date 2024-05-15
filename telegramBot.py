import telebot
import sqlite3
from telebot import types
from Check_num import check_user_num

# Инициализация бота
bot_token = '6964646666:AAG1gwMBWXE439pydC54btwBEkuqPK93dDU'
bot = telebot.TeleBot(bot_token)

# Подключение к базе данных и создание таблицы при необходимости


@bot.message_handler(commands=['start'])
def handle_start(message):
    conn = sqlite3.connect('D:\\Desktop\\git_GLPI\\glpi-dev\\users_info.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id_tg INTEGER, phone_number TEXT, password TEXT)''')
    conn.commit()
    
    bot.send_message(message.chat.id, "Пожалуйста, введите свой номер телефона:")
    bot.register_next_step_handler(message, handle_phone_input)

  

def handle_phone_input(message):

    conn = sqlite3.connect('D:\\Desktop\\git_GLPI\\glpi-dev\\users_info.db')
    cur = conn.cursor()

    phone_number = message.text
    data = check_user_num(phone_number)

    
    if data:

        # Получаем ID пользователя
        user_id = message.from_user.id

        # Проверяем, есть ли уже пользователь с таким ID в базе данных
        cur.execute("SELECT * FROM Users WHERE user_id_tg = ?", (user_id,))
        existing_user = cur.fetchone()
        

        if existing_user:
            # Если номер пользователя привязан к ID

            bot.register_next_step_handler(message, handle_password_input)
            
        else:
            # Добавляем нового пользователя в базу данных

            cur.execute("INSERT INTO Users (user_id_tg, phone_number) VALUES (?, ?)", (user_id, phone_number))
            conn.commit()
            bot.send_message(message.chat.id, "Номер успешно добавлен к вашему ID, пожалуйста, введите пароль:")
            bot.register_next_step_handler(message, handle_password_input)

        
    else:
        bot.send_message(message.chat.id, "Номер не найден в системе")

    cur.close()
    conn.close()
    
    

def handle_password_input(message):
    # password = message.text
    bot.send_message(message.chat.id, "Разработка в процессе!")  
    # # Добавляем пароль пользователя в базу данных
    # user_id = message.from_user.id
    # cursor.execute("UPDATE Users SET password = ? WHERE user_id = ?", (password, user_id))
    # conn.commit()

    # # Отправляем пользователю сообщение о том, что пароль успешно добавлен
    # bot.send_message(message.chat.id, "Пароль успешно добавлен. Отправьте его для проверки.")

# Другие обработчики команд и логика бота

# Запуск бота
bot.polling()

