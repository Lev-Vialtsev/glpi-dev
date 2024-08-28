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
last_timestamp = 1
session_token = glpil.init_session()

#  Telebot
bot_token = config['TELEGRAM']['token']
chat_id = config['TELEGRAM']['chat_id']
topic_id = int(config['TELEGRAM']['topic_id'])
production = config['TELEGRAM']['production']
bot = telebot.TeleBot(bot_token)

# --- LOGGING ---
log_file = config['LOG']['logfile']
log_level = config['LOG']['log_level'].upper()

# Преобразование уровня логирования из строки в числовое значение
log_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
log_level_num = log_level_map.get(log_level, logging.INFO)

logging.basicConfig(
    filename=log_file,
    level=log_level_num,
    format='%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s() %(levelname)s - %(message)s'
)


# =-=-=-=-=-=-= Создание базы данных, считывание времени =-=-=-=-=-=-=
def get_task_time():
    conn = sqlite3.connect(config['DATABASE']['db_path'])
    cur = conn.cursor()

    # Создание таблицы (если ее еще нет)
    res = cur.execute('''CREATE TABLE IF NOT EXISTS
    tasks_notifications 
    (task_id INTEGER,
    time_task_creation TEXT)''')

    # Проверка результата создания таблицы
    if res.rowcount == 0:
        # Таблица уже существует, поэтому нет новых записей
        logging.info("Таблица tasks_notifications уже существует.")
    else:
        # Таблица создана, вывести информацию в лог
        logging.info("Таблица tasks_notifications создана.")

    try:
        cur.execute("SELECT time_task_creation FROM tasks_notifications")
        result = cur.fetchone()
    except sqlite3.OperationalError as e:
        # Обработка ошибки: 
        # 1. Вывод ошибки в лог
        logging.error(f'Ошибка при чтении базы данных: {e}')
        # 2. Проверка, не связано ли это с отсутствием колонки
        if 'no such column' in str(e):
            # 3. Обновление схемы таблицы (добавление колонки)
            cur.execute("ALTER TABLE tasks_notifications ADD COLUMN time_task_creation TEXT")
            conn.commit()  # Сохранение изменений в схеме
            # 4. Повторный запрос к базе данных
            cur.execute("SELECT time_task_creation FROM tasks_notifications")
            result = cur.fetchone()
        else:
            # 5. Если ошибка не связана с колонкой, вывести предупреждение в лог
            logging.warning('Ошибка в функции get_task_time(), не связанная с отсутствием колонки.')

    logging.debug('База данных создана')

    return cur, conn, result


# =-=-=-=-=-=-= Сортирвка списка заявок =-=-=-=-=-=-=
def sorter(session_token, result, production, cur, conn):  # Добавлен параметр production
    existence = 0
    sorted_tasks = []
    filtered_tasks = []  # Новый список для отфильтрованных задач

    if result:
        last_timestamp = result[0]
    else:
        # Если значение пустое, берем текущее время минус 1 час
        now = datetime.now()
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
        existence = 0
    else:
        sorted_tasks = sorted(task["data"], key=lambda item: int(datetime.strptime(item["15"], "%Y-%m-%d %H:%M:%S").timestamp()))
        logging.debug('Список задач рассортирован')
        existence = 1

        # Фильтрация списка задач только в режиме production
        if production == 'True':

            for item in sorted_tasks:
                if item['80'] != "I > Заказчики > Рога и Копыта ООО":
                    filtered_tasks.append(item)
                    logging.debug('Задачи из организации "Рога и Копыта удалены"')
                if not filtered_tasks:
                    logging.debug('Заявок пока нет')
                    task_id = item['2']
                    last_timestamp = datetime.strptime(item['15'], "%Y-%m-%d %H:%M:%S").timestamp()
                    update_and_close_db(cur, conn, last_timestamp, task_id)

    if production == 'True':
        return existence, filtered_tasks
    else:
        return existence, sorted_tasks 


# =-=-=-=-=-=-= Получение информации о заявке =-=-=-=-=-=-=
def request_glpi(session_token, task_data):
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

    logging.debug('Информация о заявке получена')

    return task_id, task_content, autor_name, assigned_to


# =-=-=-=-=-=-= Получение переменных используемых в формировании уведомления =-=-=-=-=-=-=
def get_text_elem(task_data, task_content):
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

    logging.debug('Текст готов к формированию')

    return type, category, content


# =-=-=-=-=-=-= Формирование текста уведомления =-=-=-=-=-=-=
def do_text(task_data, autor_name, assigned_to, content, task_id, category, type):
    text =  f'{task_data["19"][-8:-3]} '
    text += f'{type} "<a href="https://task.it25.org/front/ticket.form.php?id={task_id}">'
    text += f'{task_data["1"]}</a>" \n{task_data["80"]}'
    text += f'\nИнициатор: {autor_name["firstname"]} {autor_name["realname"]}'
    text += f'\nНазначено: {assigned_to}'
    text += f'\nСрок: {category}'
    text += f'\nОписание: {content}'

    logging.debug('Текст сформирован')

    return text


# =-=-=-=-=-=-= Обновление бд и её закрытие =-=-=-=-=-=-=
def update_and_close_db(cur, conn, last_timestamp, task_id):
# Удаляем старые записи с другим task_id
    cur.execute("DELETE FROM tasks_notifications WHERE task_id != ?", (task_id,))
# Добавляем ID заявки в базу данных
    cur.execute("REPLACE INTO tasks_notifications (task_id, time_task_creation) VALUES (?, ?)", (task_id, last_timestamp))
    conn.commit()
    cur.close()
    conn.close()

    logging.debug('База данных обновлена и закрыта')


# =-=-=-=-=-=-= Main function =-=-=-=-=-=-=
def main_func(production):
    logging.info('Программа запущена')
    # Главный цикл
    while True:
        # Пауза 1 минутаx
        time.sleep(1 * 6)

        # Создание бд и получение времени создания последней заявки
        cur, conn, result = get_task_time()
        # Получение списка заявок и его сортировка по увеличению значения timestamp
        existence, sorted_tasks = sorter(session_token, result, production, cur, conn)  # Передача production в sorter

        if not existence:
            continue
        else:
            pass

        # Работа с сортированным списком заявок
        for task_data in sorted_tasks:
            # Получаем все необходимые данные о заявке с помощью API запросов
            task_id, task_content, autor_name, assigned_to = request_glpi(session_token, task_data)
            # Получаем текстовые элементы уведомления
            type, category, content = get_text_elem(task_data, task_content)
            # Группировка элементов в одно целое сообщение
            text = do_text(task_data, autor_name, assigned_to, content, task_id, category, type)
            # Отправка сообщения с уведомлением в телеграмм
            tgl.send_message(bot_token, chat_id, topic_id, text)
            logging.info(f'Отправлено сообщение о заявке {task_id}')

        # Сохранение времени создания последней заявки 
        if sorted_tasks:
            last_timestamp = datetime.strptime(sorted_tasks[-1]['15'], "%Y-%m-%d %H:%M:%S").timestamp()
            # Обновление значений и закрытие базы данных 
            update_and_close_db(cur, conn, last_timestamp, task_id)


main_func(production)