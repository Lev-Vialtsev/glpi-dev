import requests
import json
import logging
import configparser
import traceback

# --- CONFIG ---
config = configparser.ConfigParser()
config.read('notifier_config.ini')

app_token = config['API']['app_token']
user_token = config['API']['user_token']
session_token = None

# Logging
# logging.basicConfig(filename='glpi_notifications.log', 
#                     level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

'''Получение токена сессии'''


def init_session():
    global session_token, user_token
    global app_token

    url = "https://task.it25.org/apirest.php/initSession"
    # Заголовки запроса
    headers = {
        "Content-Type": "application/json",
        "App-Token": app_token
    }

    # Аутентификация с помощью токена пользователя
    headers["Authorization"] = f"user_token {user_token}"

    # Отправка запроса GET
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при отправке запроса: {e}")
        traceback.print_exc()
    else:
        data = response.json()
        if 'session_token' in data:
            session_token = data['session_token']

    return session_token

def change_active_entities(session_token):
    global app_token

    # Данные для POST запроса
    url = "https://task.it25.org/apirest.php/changeActiveEntities"
    headers = {
        "Content-Type": "application/json",
        "App-Token": app_token,
        "Session-Token": session_token
    }
    data = {
        "entities_id": 2,
        "is_recursive": True
    }

    # Отправка POST запроса
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()
        print(json.dumps(response_data, indent=4, sort_keys=True, ensure_ascii=False))
    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка при отправке запроса: {e}")


def check_user_num(session_token, phone_number):
    global app_token

    url = f"https://task.it25.org/apirest.php/search/user?criteria[0][field]=11& \
    criteria[0][searchtype]=contains&criteria[0][value]={phone_number}&criteria[1][link]=OR& \
    criteria[1][field]=6&criteria[1][searchtype]=contains&criteria[1][value]={phone_number}& \
    criteria[2][link]=OR&criteria[2][field]=10&criteria[2][searchtype]=contains&criteria[2][value]={phone_number}"

    headers = {
        "Content-Type": "application/json",
        "App-Token": app_token,
        "Session-Token": session_token
    }

    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Ошибка соединения: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
    else:
        if response.status_code == 200:
            data = response.json()
            num_finder = data['totalcount']
            return num_finder
        else:
            print(f"Ошибка при инициализации сеанса: {response.status_code} {response.text}")


def kill_session(session_token):
    global app_token
    global user_token

    # URL конечной точки
    url = "https://task.it25.org/apirest.php/killSession"

    # Заголовки запроса
    headers = {
        "Content-Type": "application/json",
        "App-Token": app_token,
        "Session-Token": session_token
    }

    # Аутентификация с помощью токена пользователя
    headers["Authorization"] = f"user_token {user_token}"

    # Отправка запроса GET
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Ошибка соединения: {e}")
    except requests.exceptions.NameResolutionError as e:
        print(f"Ошибка разрешения имени: {e}")
    else:
        # Проверка ответа
        if response.status_code == 200:
            # Получение токена сеанса
            data = response.json()
            print(json.dumps(data, indent=4, sort_keys=True,ensure_ascii=False))
        else:
            print(f"Ошибка при инициализации сеанса: {response.status_code} {response.text}")


def get_existing_tasks(session_token):
    global app_token

    url = "https://task.it25.org/apirest.php/search/ticket?criteria[0][link]=AND&criteria[0][field]=15&criteria[0][searchtype]=morethan&criteria[0][value]=-15MINUTE&itemtype=Ticket&start=0"

    # Заголовки запроса
    headers = {
        "Content-Type": "application/json",
        "App-Token": app_token,
        "Session-Token": session_token
    }

    # Отправка запроса GET
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Ошибка соединения: {e}")
    except requests.exceptions.NameResolutionError as e:
        print(f"Ошибка разрешения имени: {e}")
    else:
        # Проверка ответа
        if response.status_code == 200:
            # Получение токена сеанса
            data = response.json()
            print(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))
        else:
            print(f"Ошибка при инициализации сеанса: {response.status_code} {response.text}")
    return data


def get_task_info(session_token, task_id):
    global app_token

    url_without_id = "https://task.it25.org/apirest.php/Ticket/"
    url = url_without_id + str(task_id)

    # Заголовки запроса
    headers = {
        "Content-Type":  "application/json",
        "App-Token":     app_token,
        "Session-Token": session_token
    }

    # Отправка запроса GET
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Ошибка соединения: {e}")
    except requests.exceptions.NameResolutionError as e:
        print(f"Ошибка разрешения имени: {e}")
    else:
        # Проверка ответа
        if response.status_code == 200:
            # Получение токена сеанса
            data = response.json()
            return data
            # print(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))
        else:
            print(f"Ошибка при инициализации сеанса: {response.status_code} {response.text}")


def get_user_info(session_token, user_id):
    global app_token

    url_without_id = "https://task.it25.org/apirest.php/user/"
    url = url_without_id + str(user_id)

    # Заголовки запроса
    headers = {
        "Content-Type": "application/json",
        "App-Token":     app_token,
        "Session-Token": session_token
    }

    # Отправка запроса GET
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Ошибка соединения: {e}")
    except requests.exceptions.NameResolutionError as e:
        print(f"Ошибка разрешения имени: {e}")
    else:
        # Проверка ответа
        if response.status_code == 200:
            # Получение токена сеанса
            data = response.json()
            # print(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))
        else:
            print(f"Ошибка при инициализации сеанса: {response.status_code} {response.text}")

    return data
