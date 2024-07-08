import telebot
import sqlite3
import tgl
import glpil
import logging
import traceback
import sys
import configparser

# Инициализация логгирования
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')

# Загрузка конфигурации
def loadConfig(file_name):
    config = configparser.ConfigParser()
    try:
        config.read(file_name)
        return config
    except configparser.Error as e:
        log.error(f"Ошибка при чтении конфигурационного файла: {e}")
        sys.exit(1)

# Основной блок кода
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Нужен 1 параметр - файл конфигурации")
        sys.exit(1)
    else:
        config = loadConfig(sys.argv[1])

        # Настройка уровня логгирования
        if config.getboolean("logging", "debug"):
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)

# Инициализация бота
bot_token = config.get('bot', 'token')
bot = tgl.init(bot_token)

@bot.message_handler(commands=['start'])
def handle_start(message):
    log.info(f"Обработка команды '/start' от пользователя {message.from_user.id}")

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
    log.info(f"Пользователь {message.from_user.id} нажал кнопку 'Start'")

    bot.send_message(message.chat.id, "Пожалуйста, введите свой номер телефона:")
    bot.register_next_step_handler(message, handle_phone_input)

def handle_phone_input(message):
    log.info(f"Пользователь {message.from_user.id} ввел номер телефона: {message.text}")

    conn = sqlite3.connect("C:\\Users\\Admin\\Desktop\\DataBases\\glpi_db.db")
    cur = conn.cursor()

    phone_number = message.text

    try:
        session_token = glpil.init_session()
        data = glpil.check_user_num(session_token, phone_number)

        if data:
            log.info(f"Номер телефона {phone_number} найден в системе для пользователя {message.from_user.id}")
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
            log.info(f"Номер телефона {phone_number} не найден в системе для пользователя {message.from_user.id}")
            bot.send_message(message.chat.id, "Номер не найден в системе")
            glpil.kill_session(session_token)

    except Exception as e:
        log.error(f"Ошибка при обработке номера телефона: {e}")
        traceback.print_exc()
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

    finally:
        cur.close()
        conn.close()

# Запуск бота
bot.polling()
