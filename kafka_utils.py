from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, errors
import os
import asyncio
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError
import asyncio


KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")


async def create_kafka_topic(topic_name, num_partitions=1, replication_factor=1):
    """Create a Kafka topic using aiokafka."""
    admin_client = AIOKafkaAdminClient(bootstrap_servers=KAFKA_BROKER)
    await admin_client.start()
    try:
        topic = NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)
        await admin_client.create_topics([topic])
        print(f"Topic '{topic_name}' created successfully.")
    except TopicAlreadyExistsError:
        print(f"Topic '{topic_name}' already exists.")
    except Exception as e:
        print(f"Failed to create topic '{topic_name}': {e}")
    finally:
        await admin_client.close()


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
