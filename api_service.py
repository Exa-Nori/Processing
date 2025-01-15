from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from aiokafka import AIOKafkaProducer
import asyncio
import json
import os
from kafka_utils import create_kafka_consumer, close_kafka_consumer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")

scenarios = {}
next_scenario_id = 1
producer = None

class Scenario(BaseModel):
    id: int
    status: str
    params: dict

class ScenarioCreateRequest(BaseModel):
    params: dict

class ScenarioStatusUpdateRequest(BaseModel):
    status: str

async def lifespan(app: FastAPI):
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=[KAFKA_BROKER])
    await producer.start()
    print("Kafka producer started successfully.")
    yield
    await producer.stop()
    print("Kafka producer stopped successfully.")

app = FastAPI(lifespan=lifespan)

@app.post("/scenario")
async def create_scenario(request: ScenarioCreateRequest):
    global next_scenario_id
    scenario_id = next_scenario_id
    next_scenario_id += 1

    scenario = Scenario(id=scenario_id, status="inactive", params=request.params)
    scenarios[scenario_id] = scenario

@app.get("/scenarios")
async def list_scenarios():
    """List all scenarios."""
    return list(scenarios.values())

@app.get("/scenario/{id}")
async def get_scenario(id: int):
    scenario = scenarios.get(id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@app.put("/scenario/{id}/status")
async def update_status(id: int, request: ScenarioStatusUpdateRequest):
    """Update the status of a specific scenario."""
    scenario = scenarios.get(id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    scenario.status = request.status
    return {"message": f"Status updated to '{request.status}' for scenario {id}"}

@app.put("/scenario/{id}/state")
async def change_state(id: int, state: str = Query(..., regex="^(start|stop)$")):
    """Initiates start/stop for a scenario, changing its status accordingly."""
    print(f"Received change_state request: id={id}, state={state}")

    scenario = scenarios.get(id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    new_status = "active" if state == "start" else "inactive"
    scenario.status = new_status
    
    command = {"action": state, "scenario_id": id}
    await producer.send_and_wait("state-change-commands", value=json.dumps(command).encode("utf-8"))
    return {"message": f"State change to '{state}' (status '{new_status}') initiated for scenario {id}"}

@app.get("/status")
async def system_health():
    return {"status": "OK"}

@app.get("/health")
async def health():
    try:
        consumer = await create_kafka_consumer("test-topic")
        await close_kafka_consumer(consumer)
        return {"status": "healthy"}
    except Exception:
        return {"status": "unhealthy"}
