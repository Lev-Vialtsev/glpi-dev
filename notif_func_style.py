import glpil
import tgl
import time
import sqlite3
import telebot
import logging
import configparser
from datetime import datetime, timedelta
import traceback
import sys

# --- CONFIG ---
config = configparser.ConfigParser()
config.read('notifier_config.ini')
last_timestamp = 1
session_token = glpil.init_session()
required_version = 1

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


# =-=-=-=-=-=-= Запуск обновления/создания бд =-=-=-=-=-=-=
def update_db_version(required_version):
    current_version = 0
    conn = sqlite3.connect(config['DATABASE']['db_path'])
    cur = conn.cursor()

    # Получаем текущую версию из таблицы Params
    try:
        cur.execute("SELECT db_version FROM Params LIMIT 1")
        current_version = cur.fetchone()[0]    # Наконец-то пригодилась индексация!!!
        if current_version is None:
            current_version = 0
            logging.warning('Значение оказалось пустым')
    except Exception as e:
        logging.warning(f'Не удалось получить версию базы: {traceback.format_exc()}')
        current_version = 0

    # Обновляем версию базы данных, если необходимо
    while current_version < required_version:
        # Выполняем изменения для каждой новой версии
        if apply_changes_for_version(conn, current_version) == False:
            logging.critical("apply_changes_for_version() - return error")
            return None, None

        current_version += 1

        # Обновляем номер версии в таблице Params
        try:
            cur.execute("UPDATE Params SET db_version = ?", (current_version,))
            conn.commit()
        except Exception as e:
            logging.error(f'Ошибка обновления версии в базе: {traceback.format_exc()}')
            return None, None


    return conn, cur 


# =-=-=-=-=-=-= Обновление версии бд =-=-=-=-=-=-=
def apply_changes_for_version(conn, version):
    
    cur = conn.cursor()

    # Изменения для каждой версии. 
    if version == 0:

        # Создание таблицы Params и запись версии:
        try:
            cur.execute('''
                    CREATE TABLE IF NOT EXISTS Params (
                        id INTEGER PRIMARY KEY,
                        db_version INTEGER NOT NULL
                    )
                ''')
        except Exception as e:
            logging.error(f'Ошибка создания таблицы Params: {traceback.format_exc()}')


        # Проверяем, существует ли таблица tasks_notifications.
        try:
            cur.execute('''
                    CREATE TABLE IF NOT EXISTS tasks_notifications (
                        task_id INTEGER,
                        time_task_creation TEXT
                    )
                ''')
        except Exception as e:
            logging.error(f'Ошибка создания таблицы tasks_notifications: {traceback.format_exc()}')

    elif version == 1:
        # Меняем базу с Версии 1 на 2
        pass
        

# =-=-=-=-=-=-= Cчитывание времени создания последней заявки =-=-=-=-=-=-=
def get_task_time(cur): 
    # Читаем данные из таблицы
    try:
        cur.execute("SELECT time_task_creation FROM tasks_notifications")
        result = cur.fetchone()

        if result is None:
            now = datetime.now()
            result = datetime.strptime((now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S").timestamp()
            return result

        if result:
            return result[0]
        
    except Exception as e:
        logging.error(f'Ошибка получения времени создания задачи: {traceback.format_exc()}')
        return None


# =-=-=-=-=-=-= Сортирвка списка заявок =-=-=-=-=-=-=
def sorter(session_token, result, production, cur, conn):
    existence = 0
    sorted_tasks = []
    filtered_tasks = []
    try:
        if result:
            last_timestamp = result
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
        except TypeError:
            # Если значение пустое, берем текущее время минус 1 час
            now = datetime.now()
            last_timestamp = datetime.strptime((now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S").timestamp()
            task = glpil.get_existing_tasks(session_token, float(last_timestamp))

        # Сортировка заявок по времени создания если есть новые заявки
        if task['count'] == 0:
            logging.debug('Заявок пока нет')
            existence = 0
        else:
            try:
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
            except Exception as e:
                logging.error(f'Ошибка обработки списка задач: {traceback.format_exc()}')

    except Exception as e:
        logging.error(f'Ошибка обработки списка задач: {traceback.format_exc()}')

    if production == 'True':
        return existence, filtered_tasks
    else:
        return existence, sorted_tasks 
    

# =-=-=-=-=-=-= Получение информации о заявке =-=-=-=-=-=-=
def request_glpi(session_token, task_data):
    # Получаем ID заявки
    task_id = task_data["2"]
    # Получаем информацию о конкретной заявке
    try:
        task_content = glpil.get_task_info(session_token, task_id)
    except Exception as e:
        logging.error(f'Ошибка получения информации о заявке: {traceback.format_exc()}')
        return None, None, None, None

    # Получаем инфорамцию о пользователе который создал заявку
    try:
        autor_name = glpil.get_user_info(session_token, task_content['users_id_recipient'])
    except Exception as e:
        logging.error(f'Ошибка получения информации о пользователе: {traceback.format_exc()}')
        return None, None, None, None

    # Получаем информацию о назначенном пользователе
    assigned_to = ''
    if type(task_data["5"]) == str:
        try:
            assigned_info = glpil.get_user_info(session_token, task_data["5"])
            # Получаем строку с именем и фамилией назначенного пользователя
            assigned_to = assigned_info['firstname'] + ' ' + assigned_info['realname']
        except Exception as e:
            logging.error(f'Ошибка получения информации о назначенном пользователе: {traceback.format_exc()}')
            return None, None, None, None
    else:
        try:
            for i in range(len(task_data["5"])):
                assigned_info = glpil.get_user_info(session_token, task_data["5"][i])
                # Получаем строку с именем и фамилией назначенного пользователя
                assigned_to += f'{i + 1}: '
                assigned_to += str(assigned_info['firstname']) + str(assigned_info['realname'])
        except Exception as e:
            logging.error(f'Ошибка получения информации о назначенном пользователе: {traceback.format_exc()}')
            return None, None, None, None

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

    else: 
        type = None

# Получаем текст описания заявки
    content_text = task_content['content']

# Проверка категории задачи
    if task_content['itilcategories_id'] == 1:
        category = '0:Решить сегодня'
    elif task_content['itilcategories_id'] == 2:
        category = '1:Решить завтра'
    elif task_content['itilcategories_id'] == 3:
        category = '7:Решить за неделю'
    
    else: 
        category = None

# Удаление символов разметки HTML
    try:
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
    except Exception as e:
        logging.error(f'Ошибка при обработке текста: {traceback.format_exc()}')

        

    logging.debug('Текст готов к формированию')

    return type, category, content


# =-=-=-=-=-=-= Формирование текста уведомления =-=-=-=-=-=-=
def create_message_task(task_data, autor_name, assigned_to, content, task_id, category, type):
    try:
        text = f'{type} "<a href="https://task.it25.org/front/ticket.form.php?id={task_id}">'
        text += f'{task_data["1"]}</a>" \nID: {task_id} \n{task_data["80"]}'
        text += f'\nИнициатор: {autor_name["firstname"]} {autor_name["realname"]}'
        text += f'\nНазначено: {assigned_to}'
        text += f'\nСрок: {category}'
        text += f'\nОписание: {content}'
    except Exception as e:
        logging.error(f'Ошибка в составлении текста уведомления: {traceback.format_exc()}')
        #TODO log error
        return None

    logging.debug('Текст сформирован')

    return text


# =-=-=-=-=-=-= Обновление бд и её закрытие =-=-=-=-=-=-=
def update_and_close_db(cur, conn, last_timestamp, task_id):
    try:
        cur.execute("""
      INSERT OR REPLACE INTO tasks_notifications (task_id, time_task_creation) 
      VALUES (?, ?)
    """, (task_id, last_timestamp))
    except Exception as e:
        logging.error(f'Ошибка обновления данных в базе: {traceback.format_exc()}')

    conn.commit() # Сохраняем изменения
    cur.close() # Закрываем курсор
    conn.close() # Закрываем соединение

    logging.debug('База данных обновлена и закрыта.')


# =-=-=-=-=-=-= Main function =-=-=-=-=-=-=
def main_func(production):
    logging.info('Программа запущена')
    try:
        # Главный цикл
        while True:
            # Пауза 1 минута
            time.sleep(1 * 6)
            # Создание бд и получение времени создания последней заявки
            conn, cur = update_db_version(required_version)
            if conn is None or cur is None:
                logging.critical('Проблема с обновлением версии базы')
                return False

            result = get_task_time(cur)
            # Получение списка заявок и его сортировка по увеличению значения timestamp
            existence, sorted_tasks = sorter(session_token, result, production, cur, conn)

            if not existence:
                logging.debug('Заявок пока нет')
                continue
            else:
                pass

            # Работа с сортированным списком заявок
            for i, task_data in enumerate(sorted_tasks):

                # Получаем все необходимые данные о заявке с помощью API запросовw
                task_id, task_content, autor_name, assigned_to = request_glpi(session_token, task_data)

                if task_id is None and task_content is None and autor_name is None and assigned_to is None:
                    logging.warning('При получении данных из GLPI произошла ошибка')
                    text = "Появилась новая заявка, но по неведомым обстоятельствам уведомление не сформировано :'("
                    tgl.send_message(bot_token, chat_id, topic_id, text)
                    continue

                # Получаем текстовые элементы уведомления
                type, category, content = get_text_elem(task_data, task_content)
                if content is None:
                    logging.warning('При формировании текста произошла ошибка.')
                    text = "Появилась новая заявка, но по неведомым обстоятельствам уведомление не сформировано :'("
                    tgl.send_message(bot_token, chat_id, topic_id, text)
                    continue

                # Группировка элементов в одно целое сообщение
                text = create_message_task(task_data, autor_name, assigned_to, content, task_id, category, type)
                if text is None:
                    logging.warning('При составлении текста для уведомления произошла ошибка.')
                    text = "Появилась новая заявка, но по неведомым обстоятельствам уведомление не сформировано :'("
                    tgl.send_message(bot_token, chat_id, topic_id, text)
                    continue

                # Отправка сообщения с уведомлением в телеграмм
                tgl.send_message(bot_token, chat_id, topic_id, text)
                logging.info(f'Отправлено сообщение о заявке {task_id}')

                # Проверка на последний элемент в цикле
                if i + 1 == len(sorted_tasks):
                    print(1, 1, 1, 1, 1, sep='\n')
                    # Сохранение времени создания последней заявки 
                    last_timestamp = datetime.strptime(sorted_tasks[-1]['15'], "%Y-%m-%d %H:%M:%S").timestamp()
                    # Обновление значений и закрытие базы данных 
                    update_and_close_db(cur, conn, last_timestamp, task_id)

    except Exception as e:
        logging.critical(f'Ошибка препятствующая выполнению главного цикла: {traceback.format_exc()}')
        return False

    return True


if __name__ == '__main__':

    if main_func(production) == False:
        logging.critical('main function global error')
        sys.exit(1)
    else:
        logging.info('programm exit success')
        sys.exit(0)
        