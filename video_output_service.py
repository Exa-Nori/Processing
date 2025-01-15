from kafka_utils import create_kafka_consumer, close_kafka_consumer
import cv2
import numpy as np
import json
import os
import asyncio
import time

PREDICTION_TOPIC = "predicted-frames"
OUTPUT_FOLDER = "output_frames"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

async def save_frame(frame_data, filename):
    """Save a decoded image frame to disk."""
    frame = np.frombuffer(frame_data, dtype=np.uint8)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    cv2.imwrite(filename, frame)
    print(f"Saved frame to {filename}")

async def main():
    # Initialize Kafka consumer asynchronously
    consumer = await create_kafka_consumer(PREDICTION_TOPIC, group_id="video-output-group")
    print("Video Output Service is running...")

    try:
        # Consume messages asynchronously
        async for message in consumer:
            try:
                data = json.loads(message.value)
                frame_data = data.get("frame_data")
                prediction_info = data.get("predictions")

                if frame_data:
                    # Process the frame and save it with a unique timestamp
                    timestamp = int(time.time())
                    filename = os.path.join(OUTPUT_FOLDER, f"frame_{timestamp}.jpg")
                    await save_frame(frame_data, filename)

                if prediction_info:
                    print(f"Predictions: {prediction_info}")

            except json.JSONDecodeError:
                print("Received an invalid JSON message.")
            except Exception as e:
                print(f"Error processing frame: {str(e)}")
    finally:
        # Ensure the consumer is closed on exit
        await close_kafka_consumer(consumer)

# Run the main function asynchronously
if __name__ == "__main__":
    asyncio.run(main())
