import glpil
import tgl
import time
import sqlite3
import telebot

bot = telebot.TeleBot('6964646666:AAG1gwMBWXE439pydC54btwBEkuqPK93dDU')

while True:

    conn = sqlite3.connect('C:\\Users\\Admin\\Desktop\\DataBases\\glpi_db.db')
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

    

    for i in range(task['count']):
        task_id = task['data'][i]['2']  # Получаем ID заявки

        task_content = glpil.get_task_info(session_token, task_id)

        autor_name = glpil.get_user_info(session_token, task_content['users_id_recipient'])

        # Проверяем, есть ли ID заявки в базе данных
        cur.execute("SELECT 1 FROM tasks_notifications WHERE task_id = ?", (task_id,))
        exists = cur.fetchone()

        if not exists:  # Если ID заявки нет в базе данных

            flag = True
            content = ''
            count_simbols = -1

            if task["data"][i]["14"] == 1:
                type = 'инцидент'
            else:
                type = 'запрос'
            

            content_text = task_content['content']

            for j in range(len(content_text)):  # Изменили i на j
                if content_text[j:j+5] == '&#60;':
                    flag = False
                    count_simbols = -1
                if not flag:
                    count_simbols += 1
                if content_text[j:j+5] == '&#62;':
                    flag = True
                if flag:
                    content += content_text[j]

                # Удаление лишних символов '&#62;' после цикла
            content = content.replace('&#62;', '')


            text = f'{task["data"][i]["19"][-8:-3]} {type} "<a href=\"https://task.it25.org/front/ticket.form.php?id={task_id}\">{task["data"][i]["1"]}</a>" \n {task["data"][i]["80"]} \n Автор: {autor_name['firstname']} {autor_name['realname']} \n Описание: {content}'


            tgl.send_message('6964646666:AAG1gwMBWXE439pydC54btwBEkuqPK93dDU', '-1002234256199', 2, text)
            # bot.send_message('-1002234256199', text)

            # Добавляем ID заявки в базу данных
            cur.execute("INSERT INTO tasks_notifications (task_id) VALUES (?)", (task['data'][i]['2'],))

    conn.commit()
    cur.close()
    conn.close()

    # Пауза на 15 минут
    time.sleep(1 * 60)  # 15 минут в секундах
