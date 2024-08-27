import glpil
import tgl
import time
import sqlite3
import telebot
import logging
import configparser
from datetime import datetime, timedelta


# --- CONFIG ---
config = configparser.ConfigParser()
config.read('notifier_config.ini')
log_file = config['LOG']['logfile']
last_timestamp = 1
new_timestamp = 1
session_token = '0'

#  Telebot
bot_token = config['TELEGRAM']['token']
chat_id = config['TELEGRAM']['chat_id']
topic_id = int(config['TELEGRAM']['topic_id'])
production = config['TELEGRAM']['production']
bot = telebot.TeleBot(bot_token)

# Logging
logging.basicConfig(filename=log_file,
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- MAIN ---
while True:
    # Create DB and tables
    conn = sqlite3.connect(config['DATABASE']['db_path'])
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS
    tasks_notifications 
    (task_id INTEGER,
    time_task_creation TEXT)''')

    # Получаем значение time_task_creation из базы данных

    cur.execute("SELECT time_task_creation FROM tasks_notifications")
    result = cur.fetchone()

    if result:
        last_timestamp = result[0]
        # last_timestamp = datetime.strptime(time_task_creation, "%Y-%m-%d %H:%M:%S").timestamp()
    else:
        # Если значение пустое, берем текущее время минус 1 час
        now = datetime.now()
        # time_task_creation = (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        last_timestamp = datetime.strptime((now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S").timestamp()

    # Получение списка заявок
    try:
        task = glpil.get_existing_tasks(session_token, float(last_timestamp))
    except NameError:
        session_token = glpil.init_session()
        task = glpil.get_existing_tasks(session_token, float(last_timestamp))

    # Сортировка заявок по времени создания если есть новые заявки
    if task['count'] == 0:
        logging.debug('Заявок пока нет')
    else:
        sorted_tasks = sorted(task["data"], key=lambda item: int(datetime.strptime(item["15"], "%Y-%m-%d %H:%M:%S").timestamp()))

        # Обработка отсортированного списка заявок
        for task_data in sorted_tasks:

            # Проверка режима бота. В случае режима продакшн - заявки из организации рога и копыта не будут отсылаться в уведомления.
            if not production and 'Рога и Копыта' in task_data["80"]:
                logging.info('Вы в режиме продакшн, заявка написанная в организации "Рога и Копыта" не будет отправлена')
                continue

            else:
                logging.info('Вы в режиме тестирования, написана заявка в организации "Рога и Копыта"')

            # Получаем ID заявки
            task_id = task_data['2']
            # Получаем информацию о конкретной заявке
            task_content = glpil.get_task_info(session_token, task_id)
            # Получаем инфорамцию о пользователе который создал заявку
            autor_name = glpil.get_user_info(session_token, task_content['users_id_recipient'])
            # Получаем время создания последней заявки
            time_task_creation = task_data['15']
            new_timestamp = datetime.strptime(time_task_creation, "%Y-%m-%d %H:%M:%S").timestamp()

            # Получаем информацию о назначенном пользователе
            assigned_to = ''
            if type(task_data["5"]) == str:
                assigned_info = glpil.get_user_info(session_token, task_data["5"])
                # Получаем строку с именем и фамилией назначенного пользователя
                assigned_to = assigned_info['firstname'] + ' ' + assigned_info['realname']
            else:
                for i in range(len(task_data["5"])):
                    assigned_info = glpil.get_user_info(session_token, task_data["5"][i])
                    # Получаем строку с именем и фамилией назначенного пользователя
                    assigned_to += f'{i + 1}: '
                    assigned_to += f'{assigned_info['firstname']} {assigned_info['realname']} '

    # Начало обработкиз заявки
            flag = True
            content = ''
            count_simbols = -1

    # Проверка типа заявки
            if task_data["14"] == 1:
                type = 'Инцидент'
            elif task_data["14"] == 2:
                type = 'Запрос'

    # Получаем текст описания заявки
            content_text = task_content['content']

    # Проверка категории задачи
            if task_content['itilcategories_id'] == 1:
                category = '0:Решить сегодня'
            elif task_content['itilcategories_id'] == 2:
                category = '1:Решить завтра'
            elif task_content['itilcategories_id'] == 3:
                category = '7:Решить за неделю'

    # Удаление символов разметки HTML
            for j in range(len(content_text)):
                if content_text[j:j+5] == '&#60;':
                    flag = False
                    count_simbols = -1
                if not flag:
                    count_simbols += 1
                if content_text[j:j+5] == '&#62;':
                    flag = True
                if flag:
                    content += content_text[j]
            content = content.replace('&#62;', '')

    # Формирование текста уведомления
            text =  f'{task_data["19"][-8:-3]} '
            text += f'{type} "<a href="https://task.it25.org/front/ticket.form.php?id={task_id}">'
            text += f'{task_data["1"]}</a>" \n{task_data["80"]}'
            text += f'\nИнициатор: {autor_name["firstname"]} {autor_name["realname"]}'
            text += f'\nНазначено: {assigned_to}'
            text += f'\nСрок: {category}'
            text += f'\nОписание: {content}'

    # Отправка сообщения в телеграмм
            tgl.send_message(bot_token, chat_id, topic_id, text)
            logging.info(f'Отправлено сообщение о заявке {task_id}')


        last_timestamp = datetime.strptime(sorted_tasks[-1]['15'], "%Y-%m-%d %H:%M:%S").timestamp()   # Назначаю время последней задачи в отсортированном по времени списке задач временем с последней задачи

        # Удаляем старые записи с другим task_id
        cur.execute("DELETE FROM tasks_notifications WHERE task_id != ?", (task_id,))

        # Добавляем ID заявки в базу данных
        cur.execute("REPLACE INTO tasks_notifications (task_id, time_task_creation) VALUES (?, ?)", (task_id, last_timestamp))
        
        conn.commit()
        cur.close()
        conn.close()

    # Пауза на 1 минуту
    time.sleep(1 * 60)
