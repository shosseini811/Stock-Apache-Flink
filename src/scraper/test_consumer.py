from confluent_kafka import Consumer, KafkaError
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def consume_messages():
    # Configure the Confluent Kafka consumer
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'test_consumer_group',
        'auto.offset.reset': 'earliest'  # Start from beginning for testing
    }
    
    consumer = Consumer(conf)
    consumer.subscribe(['stock_data'])
    
    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info('Reached end of partition')
                else:
                    logger.error(f'Error: {msg.error()}')
            else:
                try:
                    # Decode and parse the message
                    value = msg.value().decode('utf-8')
                    data = json.loads(value)
                    
                    # Print the received data
                    logger.info("-" * 50)
                    logger.info(f"Received stock data: {json.dumps(data, indent=2)}")
                    logger.info("-" * 50)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    logger.info("Starting Kafka consumer...")
    consume_messages()
