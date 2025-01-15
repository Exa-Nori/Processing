from kafka_utils import create_kafka_consumer, create_kafka_producer, close_kafka_producer, close_kafka_consumer
import json
import asyncio
import threading

COMMAND_TOPIC = "state-change-commands"
RUNNER_COMMAND_TOPIC = "runner-commands"

states = {
    "inactive": ["init_startup"],
    "init_startup": ["in_startup_processing"],
    "in_startup_processing": ["active"],
    "active": ["init_shutdown"],
    "init_shutdown": ["in_shutdown_processing"],
    "in_shutdown_processing": ["inactive"]
}
current_state = "inactive"
state_lock = threading.Lock()

def transition_to(new_state):
    global current_state
    with state_lock:
        if new_state in states.get(current_state, []):
            print(f"Transitioning from {current_state} to {new_state}")
            current_state = new_state
            return True
        else:
            print(f"Invalid transition from {current_state} to {new_state}")
            return False

async def send_runner_command(producer, action):
    """Helper function to send start/stop command to runner service asynchronously."""
    command = {"action": action}
    await producer.send_and_wait(RUNNER_COMMAND_TOPIC, value=json.dumps(command).encode("utf-8"))
    print(f"Orchestrator sent '{action}' command to runner.")

async def process_command(command, producer):
    global current_state
    action = command.get("action")
    if action == "start":
        if transition_to("init_startup"):
            await asyncio.sleep(1)
            transition_to("in_startup_processing")
            await asyncio.sleep(1)
            transition_to("active")
            await send_runner_command(producer, "start")
    elif action == "stop":
        if transition_to("init_shutdown"):
            await asyncio.sleep(1)
            transition_to("in_shutdown_processing")
            await asyncio.sleep(1)
            transition_to("inactive")
            await send_runner_command(producer, "stop")
    else:
        print(f"Unknown command action: {action}")


async def main():
    consumer = await create_kafka_consumer(COMMAND_TOPIC, group_id="orchestrator-group")
    producer = await create_kafka_producer()

    print("Orchestrator is running...")

    try:
        async for message in consumer:
            try:
                command = json.loads(message.value)
                print(f"Orchestrator received command: {command}")
                await process_command(command, producer)
            except json.JSONDecodeError:
                print("Received an invalid JSON message.")
            except Exception as e:
                print(f"Error processing command: {str(e)}")
    finally:
        await close_kafka_producer(producer)
        await close_kafka_consumer(consumer)

if __name__ == "__main__":
    asyncio.run(main())