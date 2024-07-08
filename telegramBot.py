import telebot, sqlite3, tgl, glpil, logging, traceback, sys, configparser

# Инициализация бота

bot_token = '6964646666:AAG1gwMBWXE439pydC54btwBEkuqPK93dDU'

bot = tgl.init(bot_token)



@bot.message_handler(commands=['start'])
def handle_start(message):
    conn = sqlite3.connect("C:\\Users\\Admin\\Desktop\\DataBases\\glpi_db.db")
    cur = conn.cursor()

    # Создание таблицы Sessions (если не существует)
    cur.execute('''CREATE TABLE IF NOT EXISTS Sessions (
        session_id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES Users (user_id) ON DELETE SET NULL ON UPDATE RESTRICT,
        session TEXT
    )''')

    # Создание триггера (если не существует)
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS new_user_session
        AFTER INSERT ON Users
        BEGIN
           INSERT INTO Sessions (user_id) VALUES (NEW.user_id);
        END;
    """)

    # Создание таблицы Users (если не существует)
    cur.execute('''CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY,
        user_login TEXT,
        user_login_f INTEGER,
        user_token TEXT,
        phone NUMERIC,
        phone_field TEXT
    )''')

    conn.commit()
    cur.close()
    conn.close()

    # Отправка сообщения с кнопкой "Start"
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtn = telebot.types.KeyboardButton("Start")
    markup.add(itembtn)
    bot.send_message(message.chat.id, "Привет! Нажмите кнопку Start, чтобы начать:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Start")
def handle_start_button(message):
    bot.send_message(message.chat.id, "Пожалуйста, введите свой номер телефона:")
    bot.register_next_step_handler(message, handle_phone_input)
  

def handle_phone_input(message):
    conn = sqlite3.connect("C:\\Users\\Admin\\Desktop\\DataBases\\glpi_db.db")
    cur = conn.cursor()
    
    phone_number = message.text

    session_token = glpil.init_session()

    data = glpil.check_user_num(session_token, phone_number)

    if data:

        glpil.kill_session(session_token)


        # Получаем ID пользователя
        user_id = message.from_user.id

        # Проверяем, есть ли уже пользователь с таким ID в базе данных
        cur.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
        existing_user = cur.fetchone()
        

        if existing_user:

            cur.execute("SELECT * FROM Users WHERE user_id = ? AND phone = ?", (user_id, phone_number))
            have_phone_number = cur.fetchone()

            if have_phone_number:
                # Если номер пользователя привязан к ID
                bot.send_message(message.chat.id, "Ваш номер найден в системе!")
            else:
                cur.execute("UPDATE Users SET phone = ? WHERE user_id = ?", (phone_number, user_id))
                bot.send_message(message.chat.id, "Ваш номер успешно добавлен в систему!")

        else:
            # Добавляем нового пользователя в базу данных

            cur.execute("INSERT INTO Users (user_id, phone) VALUES (?, ?)", (user_id, phone_number))
            conn.commit()
            bot.send_message(message.chat.id, "Вы успешно добавлены в систему!")

    else:
        bot.send_message(message.chat.id, "Номер не найден в системе")

        glpil.kill_session(session_token)

    cur.close()
    conn.close()
    
    




# def loadConfig(file_name):
#     config = configparser.ConfigParser()
#     config.read(file_name)
#     return config

# if __name__ == '__main__':
#     if len(sys.argv) < 2:
#         print("need 1 param - config file")
#         sys.exit(1)
#     else:
#         config = loadConfig(sys.argv[1])
#     log=logging.getLogger("telegram-bot-reaction")

#     if config["logging"]["debug"].lower()=="yes":
#         log.setLevel(logging.DEBUG)
#     else:
#         log.setLevel(logging.INFO)

#     # create the logging file handler
#     #fh = logging.FileHandler(config.log_path)
#     fh = logging.handlers.TimedRotatingFileHandler(config["logging"]["log_path"], when=config["logging"]["log_backup_when"], backupCount=int(config["logging"]["log_backup_count"]), encoding='utf-8')
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s() %(levelname)s - %(message)s')
#     fh.setFormatter(formatter)

#     # if config["logging"]["debug"].lower()=="yes":
#     # логирование в консоль:
#     stdout = logging.StreamHandler(sys.stdout)
#     stdout.setFormatter(formatter)
#     log.addHandler(stdout)

#     # add handler to logger object
#     log.addHandler(fh)

#     log.info("Program started")
#     log.info("python version=%s"%sys.version)


# Запуск бота
bot.polling()

