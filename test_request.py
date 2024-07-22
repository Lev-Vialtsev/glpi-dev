import requests
import json

'''Получение токена сессии'''
# URL конечной точки

url = "https://task.it25.org/apirest.php/Ticket/2023072506"

# Заголовки запроса
headers = {
    "Content-Type": "application/json",
    "App-Token": "OiBm5phLf0MaJ5G2yzMjZu53Q50lb7tDtaZw0fPd", 
    "Session-Token": "i129pls9nsv12edqra35inbohj"
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
        # print('Ваша заявка под заголовком «%s», \n имеет id: %d \n Срочность: %d \n Глобальность: %d' % 
        #     (data['name'], data['id'], 
        #     data['urgency'], data['impact']))
    else:
        print(f"Ошибка при инициализации сеанса: {response.status_code} {response.text}")
        
     