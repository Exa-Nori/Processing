from kafka_utils import create_kafka_consumer, create_kafka_producer, close_kafka_producer, close_kafka_consumer
import base64
import json
import cv2
import numpy as np
from ultralytics import YOLO
import asyncio

model = YOLO('yolov5n.pt') 
FRAME_TOPIC = "video-frames"
RESULT_TOPIC = "object-detection-results"

async def process_frame(data, producer):
    """Processes a single frame for object detection and sends results."""
    try:
        frame_data = base64.b64decode(data['frame'])
        frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), -1)

        results = model(frame, conf=0.5)[0]
        detections = []
        for result in results.boxes:
            if result.cls[0] == 2:  # Class ID 2 for 'car'
                x1, y1, x2, y2 = result.xyxy[0].tolist()
                conf = result.conf[0].item()
                detections.append({
                    "x1": int(x1), "y1": int(y1),
                    "x2": int(x2), "y2": int(y2),
                    "confidence": conf
                })

        result_message = {"frame_id": data["frame_id"], "detections": detections}
        try:
            await producer.send_and_wait(RESULT_TOPIC, value=json.dumps(result_message).encode('utf-8'))
            print(f"Sent detection result for frame {data['frame_id']}")
        except:
            print("Not sent")
    except Exception as e:
        print(f"Error processing frame: {str(e)}")


async def main():
    consumer = await create_kafka_consumer(FRAME_TOPIC, group_id="object-detection-group")
    producer = await create_kafka_producer()

    print("Object Detection Service is running...")

    try:
        async for message in consumer:
            data = json.loads(message.value)
            await process_frame(data, producer)
    finally:
        await close_kafka_producer(producer)
        await close_kafka_consumer(consumer)
        print("Object Detection Service shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
