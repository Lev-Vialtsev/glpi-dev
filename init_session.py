
    
#     # OKlQa3NuZ3mVvHWObmMDmT6L03WKC0E5t9FQE9Fk мой апи-токен.

import requests
import json

'''Получение токена сессии'''
# URL конечной точки

url = "https://task.it25.org/apirest.php/initSession"

# Заголовки запроса
headers = {
    "Content-Type": "application/json",
    "App-Token": "OiBm5phLf0MaJ5G2yzMjZu53Q50lb7tDtaZw0fPd"
}

# Аутентификация с помощью токена пользователя
user_token = "OKlQa3NuZ3mVvHWObmMDmT6L03WKC0E5t9FQE9Fk"
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
        session_token = data['session_token']
        print(f"Успешно получен токен сеанса: {session_token}")
    else:
        print(f"Ошибка при инициализации сеанса: {response.status_code} {response.text}")
        
        
# -H "App-Token: OiBm5phLf0MaJ5G2yzMjZu53Q50lb7tDtaZw0fPd"
        
# h0nr9lo5tccq8dtk7o65rm4la1 токен сессии 
# cd D:\Downloads\curl-8.6.0_4-win64-mingw\curl-8.6.0_4-win64-mingw\bin
# .\curl.exe -X GET -H 'Content-Type: application/json' -H "Session-Token: h0nr9lo5tccq8dtk7o65rm4la1" -H "App-Token: OiBm5phLf0MaJ5G2yzMjZu53Q50lb7tDtaZw0fPd" 'https://task.it25.org/apirest.php/killSession'