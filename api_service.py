from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from aiokafka import AIOKafkaProducer
import asyncio
import json
import os
from kafka_utils import create_kafka_consumer, close_kafka_consumer

# Настройки Kafka
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")

# Хранилище сценариев
scenarios = {}
next_scenario_id = 1
producer = None

# Модели запросов/ответов
class Scenario(BaseModel):
    id: int
    status: str
    params: dict

class ScenarioCreateRequest(BaseModel):
    params: dict

class ScenarioStatusUpdateRequest(BaseModel):
    status: str

# Жизненный цикл приложения - автоматическое управление Kafka Producer
async def lifespan(app: FastAPI):
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=[KAFKA_BROKER])
    await producer.start()
    print("Kafka producer started successfully.")
    yield
    await producer.stop()
    print("Kafka producer stopped successfully.")

# Инициализация FastAPI
app = FastAPI(lifespan=lifespan)

# Создание сценария
@app.post("/scenario")
async def create_scenario(request: ScenarioCreateRequest):
    global next_scenario_id
    try:
        # Генерация ID для нового сценария
        scenario_id = next_scenario_id
        next_scenario_id += 1

        # Создание нового сценария
        scenario = Scenario(id=scenario_id, status="inactive", params=request.params)
        scenarios[scenario_id] = scenario  # Сохранение сценария

        # Возврат информации о созданном сценарии
        return {
            "scenario_id": scenario_id,
            "status": scenario.status,
            "params": scenario.params,
            "message": f"Сценарий {scenario_id} успешно создан"
        }
    except Exception as e:
        # Отправка сообщения об ошибке
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка создания сценария: {str(e)}"
        )

# Получение списка сценариев
@app.get("/scenarios")
async def list_scenarios():
    """Возвращает список всех сценариев."""
    return list(scenarios.values())

# Получение информации о конкретном сценарии
@app.get("/scenario/{id}")
async def get_scenario(id: int):
    scenario = scenarios.get(id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарий не найден")
    return scenario

# Обновление статуса сценария
@app.put("/scenario/{id}/status")
async def update_status(id: int, request: ScenarioStatusUpdateRequest):
    """Обновление статуса конкретного сценария."""
    scenario = scenarios.get(id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарий не найден")
    
    scenario.status = request.status
    return {"message": f"Статус сценария {id} обновлен на '{request.status}'"}

# Изменение состояния сценария (start/stop)
@app.put("/scenario/{id}/state")
async def change_state(id: int, state: str = Query(..., regex="^(start|stop)$")):
    """Изменение состояния сценария."""
    print(f"Получен запрос на изменение состояния: id={id}, state={state}")

    scenario = scenarios.get(id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарий не найден")

    new_status = "active" if state == "start" else "inactive"
    scenario.status = new_status

    # Отправка команды в Kafka
    try:
        command = {"action": state, "scenario_id": id}
        await producer.send_and_wait("state-change-commands", value=json.dumps(command).encode("utf-8"))
        return {"message": f"Изменение состояния на '{state}' (статус '{new_status}') инициировано для сценария {id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отправки команды в Kafka: {str(e)}")

# Проверка состояния системы
@app.get("/status")
async def system_health():
    return {"status": "OK"}

# Проверка здоровья Kafka
@app.get("/health")
async def health():
    try:
        consumer = await create_kafka_consumer("test-topic")
        await close_kafka_consumer(consumer)
        return {"status": "healthy"}
    except Exception:
        return {"status": "unhealthy"}
