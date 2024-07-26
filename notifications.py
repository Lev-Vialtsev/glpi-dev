import glpil
import tgl
import time
import sqlite3
import telebot
import logging
import configparser

# --- CONFIG ---
config = configparser.ConfigParser()
config.read('notifier_config.ini')

#  Telebot
bot_token = config['TELEGRAM']['token']
chat_id   = config['TELEGRAM']['chat_id']
topic_id  = int(config['TELEGRAM']['topic_id'])
production = config['TELEGRAM']['production']
bot = telebot.TeleBot(bot_token)

# Logging
logging.basicConfig(filename='glpi_notifications.log', 
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- MAIN ---
while True:

    # Create DB and tables
    conn = sqlite3.connect(config['DATABASE']['db_pase'])
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS
    tasks_notifications 
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER)''')

    # Получение списка заявок
    try:
        task = glpil.get_existing_tasks(session_token)
    except NameError:
        session_token = glpil.init_session()
        task = glpil.get_existing_tasks(session_token)

        
    # считываем все созданные заявки за последние 15 минут
    for i in range(task['count']):   

    # Проверка режима бота. В случае режима продакшн - заявки из организации рога и копыта не будут отсылаться в уведомления.
        if production and 'Рога и Копыта' in task["data"][i]["80"]:
            continue
        else:
            pass

    # Получаем ID заявки
        task_id = task['data'][i]['2']    
    # Получаем информацию о конкретной заявке
        task_content = glpil.get_task_info(session_token, task_id)   
    # Получаем инфорамцию о пользователе который создал заявку
        autor_name = glpil.get_user_info(session_token, task_content['users_id_recipient'])   
    # Получаем информацию о назначенном пользователе
        assigned_info = glpil.get_user_info(session_token, task["data"][i]["5"])   
    # Получаем строку с именем и фамилией назначенного пользователя
        assigned_to = assigned_info['firstname'] + ' ' + assigned_info['realname']   


    # Проверка наличия ID в базе
        cur.execute("SELECT 1 FROM tasks_notifications WHERE task_id = ?", (task_id,))
        exists = cur.fetchone()

    # Если ID заявки нет в базе данных
        if not exists:   
            flag = True
            content = ''
            count_simbols = -1


    # Проверка типа заявки
            if task["data"][i]["14"] == 1:
                type = 'инцидент'
            elif task["data"][i]["14"] == 2:
                type = 'запрос'

    # Получаем текст описания заявки
            content_text = task_content['content']

    # Проверка категории задачи
            if task_content['itilcategories_id'] == 1:
                category = 'Решить сегодня'
            elif task_content['itilcategories_id'] == 2:
                category = 'Решить завтра'
            elif task_content['itilcategories_id'] == 3:
                category = 'Решить за неделю'

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
            text =  f'{task["data"][i]["19"][-8:-3]} '
            text += f'{type} "<a href="https://task.it25.org/front/ticket.form.php?id={task_id}">'
            text += f'{task["data"][i]["1"]}</a>" \n{task["data"][i]["80"]}'
            text += f'\nКатегория: {category}'
            text += f'\nНазначен: {assigned_to}'
            text += f'\nАвтор: {autor_name["firstname"]} {autor_name["realname"]}\nОписание: {content}'

    # Отправка сообщения в телеграмм
            tgl.send_message(bot_token, chat_id, topic_id, text)
            logging.info(f'Отправлено сообщение о заявке {task_id}')

    # Добавляем ID заявки в базу данных
            cur.execute("INSERT INTO tasks_notifications (task_id) VALUES (?)", (task['data'][i]['2'],))

    conn.commit()
    cur.close()
    conn.close()

    # Пауза на 1 минуту
    time.sleep(1 * 60)
