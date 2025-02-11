from kafka_utils import create_kafka_consumer, close_kafka_consumer, create_kafka_topic
import cv2
import numpy as np
import json
import asyncio

PREDICTION_TOPIC = "object-detection-results"

async def display_frame(frame_data):
    """Display a single frame using OpenCV."""
    frame = np.frombuffer(frame_data, dtype=np.uint8)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    cv2.imshow("Real-Time Predictions", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Exiting video display...")
        return False  
    return True

async def main():
    await create_kafka_topic(PREDICTION_TOPIC)

    consumer = await create_kafka_consumer(PREDICTION_TOPIC, group_id="video-output-group")
    print("Video Output Service is running...")

    try:
        async for message in consumer:
            try:
                data = json.loads(message.value)
                frame_data = data.get("frame_data")
                prediction_info = data.get("predictions")

                if frame_data:
                    should_continue = await display_frame(frame_data)
                    if not should_continue:
                        break

                if prediction_info:
                    print(f"Predictions: {prediction_info}")

            except json.JSONDecodeError:
                print("Received an invalid JSON message.")
            except Exception as e:
                print(f"Error processing frame: {str(e)}")
    finally:
        await close_kafka_consumer(consumer)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(main())


# from kafka_utils import create_kafka_consumer, close_kafka_consumer
# import cv2
# import numpy as np
# import json
# import asyncio
# import av

# PREDICTION_TOPIC = "predicted-frames"

# async def setup_rtsp_stream():
#     output_container = av.open("rtsp://0.0.0.0:8554/live", mode="w", format="rtsp")
#     video_stream = output_container.add_stream("h264", rate=30)
#     video_stream.width = 640
#     video_stream.height = 480
#     video_stream.pix_fmt = "yuv420p"
#     return output_container, video_stream

# async def stream_frame(output_container, video_stream, frame_data):
#     """Stream a single frame using RTSP."""
#     frame = np.frombuffer(frame_data, dtype=np.uint8)
#     frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

#     packet = av.VideoFrame.from_ndarray(frame, format="bgr24").encode(video_stream)
#     for pkt in packet:
#         output_container.mux(pkt)

# async def main():
#     consumer = await create_kafka_consumer(PREDICTION_TOPIC, group_id="video-output-group")
#     print("Video Output Service with RTSP is running...")

#     output_container, video_stream = await setup_rtsp_stream()

#     try:
#         async for message in consumer:
#             try:
#                 data = json.loads(message.value)
#                 frame_data = data.get("frame_data")

#                 if frame_data:
#                     # Stream the frame via RTSP
#                     await stream_frame(output_container, video_stream, frame_data)

#             except json.JSONDecodeError:
#                 print("Received an invalid JSON message.")
#             except Exception as e:
#                 print(f"Error processing frame: {str(e)}")
#     finally:
#         await close_kafka_consumer(consumer)
#         output_container.close()

# if __name__ == "__main__":
#     asyncio.run(main())

