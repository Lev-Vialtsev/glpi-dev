import requests
import json

# Данные для POST запроса
url = "https://task.it25.org/apirest.php/changeActiveEntities"
headers = {
    "Content-Type": "application/json",
    "App-Token": "OiBm5phLf0MaJ5G2yzMjZu53Q50lb7tDtaZw0fPd",
    "Session-Token": "hjj7o6kv2eg8dsbt1oos0led6l"
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