import requests
import concurrent.futures
import time

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJlbWFpbCI6IjE2MDY5NTBAbGlzdC5ydSIsImV4cCI6MTc3NjcwNzExNywidHlwZSI6ImFjY2VzcyJ9.vf6McjOUTKhTw27WHKST21Ix5v0EJf2Nmgsh8e_8ns4"
BASE_URL = "http://127.0.0.1:8000/tasks"


def send_request(task_num):
    start = time.time()
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {"title": f"Задача {task_num}", "description": f"Тест многопоточности"}

    try:
        r = requests.post(BASE_URL, headers=headers, json=payload)
        print(
            f"✅ HTTP {task_num}: {r.status_code} | Ответ за {time.time()-start:.2f} сек"
        )
    except Exception as e:
        print(f"❌ Ошибка {task_num}: {e}")


if __name__ == "__main__":
    print("Отправляю 3 запроса ОДНОВРЕМЕННО...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        ex.map(send_request, [1, 2, 3])
    print("Готово!")
