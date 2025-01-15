from kafka_utils import create_kafka_consumer, create_kafka_producer, close_kafka_producer, close_kafka_consumer
import cv2
import base64
import json
import asyncio
import threading

FRAME_TOPIC = "video-frames"
RUNNER_COMMAND_TOPIC = "runner-commands"

async def read_frames(producer, stop_event):
    """Reads frames from a video file and sends them to Kafka asynchronously."""
    cap = cv2.VideoCapture("traffic.mp4")
    frame_id = 0

    while cap.isOpened() and not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Video stream ended or failed.")
            break

        _, buffer = cv2.imencode('.jpg', frame)
        frame_data = base64.b64encode(buffer).decode('utf-8')
        
        message = {"frame_id": frame_id, "frame": frame_data}
        
        try:
            await producer.send_and_wait(FRAME_TOPIC, value=json.dumps(message).encode('utf-8'))
            print(f"Sent frame {frame_id} to Kafka.")
        except Exception as e:
            print(f"Error sending frame {frame_id}: {e}")

        frame_id += 1
        await asyncio.sleep(0.1)

    cap.release()
    print("Completed frame reading and transmission.")

async def main():
    consumer = await create_kafka_consumer(RUNNER_COMMAND_TOPIC, group_id="runner-group")
    producer = await create_kafka_producer()
    stop_event = threading.Event()
    print("Runner is waiting for the start command...")

    async def handle_commands():
        """Handles start and stop commands received from Kafka."""
        nonlocal stop_event
        async for message in consumer:
            try:
                command = json.loads(message.value)
                action = command.get("action")
                if action == "start":
                    print("Received start command. Starting video processing...")
                    stop_event.clear()
                    await read_frames(producer, stop_event)
                elif action == "stop":
                    print("Received stop command. Stopping runner.")
                    stop_event.set()
            except json.JSONDecodeError:
                print("Invalid JSON message received.")
            except Exception as e:
                print(f"Error handling command: {e}")

    try:
        await handle_commands()
    finally:
        stop_event.set() 
        await close_kafka_producer(producer)
        await close_kafka_consumer(consumer)
        print("Runner shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
