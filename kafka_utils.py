from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, errors
import os
import asyncio

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")

async def create_kafka_consumer(topic, group_id="default-group"):
    for _ in range(5):
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id=group_id
            )
            await consumer.start()
            print(f"Connected to Kafka topic '{topic}' as consumer.")
            return consumer
        except Exception as e:
            print(f"Kafka consumer connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
    raise RuntimeError(f"Failed to connect to Kafka topic {topic} after retries.")


async def create_kafka_producer():
    for _ in range(5):
        try:
            producer = AIOKafkaProducer(bootstrap_servers=[KAFKA_BROKER])
            await producer.start()
            print("Connected to Kafka broker as producer.")
            return producer
        except Exception as e:
            print(f"Kafka producer connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
    raise RuntimeError("Failed to connect to Kafka producer after retries.")


async def close_kafka_producer(producer):
    """Gracefully closes the Kafka producer."""
    await producer.stop()
    print("Kafka producer stopped successfully.")

async def close_kafka_consumer(consumer):
    """Gracefully closes the Kafka consumer."""
    await consumer.stop()
    print("Kafka consumer stopped successfully.")
