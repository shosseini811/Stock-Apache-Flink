from flask import Flask, jsonify
from confluent_kafka import Consumer, KafkaError
import json
import logging
from threading import Thread
import queue
from datetime import datetime, timedelta
import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.dynamodb_manager import DynamoDBManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize DynamoDB manager
db_manager = DynamoDBManager()

# In-memory cache for latest stock data
latest_stocks = queue.Queue(maxsize=100)

class KafkaListener(Thread):
    def __init__(self, topic='processed_stock_data', bootstrap_servers=['localhost:9092']):
        Thread.__init__(self)
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.daemon = True  # Thread will exit when main program exits
        
    def run(self):
        try:
            # Configure the Confluent Kafka consumer
            conf = {
                'bootstrap.servers': self.bootstrap_servers[0],
                'group.id': 'stock_api_group',
                'auto.offset.reset': 'latest'
            }
            
            consumer = Consumer(conf)
            consumer.subscribe([self.topic])
            
            logger.info(f"Started listening to Kafka topic: {self.topic}")
            
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
                        
                        # Update the latest stocks queue
                        if latest_stocks.full():
                            latest_stocks.get()  # Remove oldest item if queue is full
                        latest_stocks.put(data)
                        
                        # Save data to DynamoDB
                        db_manager.save_price(data)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {e}")
        finally:
            consumer.close()

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    try:
        # Get limit parameter, default to 10
        limit = min(int(request.args.get('limit', 10)), 100)
        
        # Convert queue items to list
        stocks = []
        temp_queue = queue.Queue()
        
        # Get items from queue
        while not latest_stocks.empty() and len(stocks) < limit:
            item = latest_stocks.get()
            stocks.append(item)
            temp_queue.put(item)
            
        # Put items back in queue
        while not temp_queue.empty():
            latest_stocks.put(temp_queue.get())
            
        return jsonify({
            'status': 'success',
            'data': stocks,
            'count': len(stocks)
        })
    except Exception as e:
        logger.error(f"Error serving request: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stock/latest', methods=['GET'])
def get_latest_stock():
    # Try to get data from DynamoDB first
    db_data = db_manager.get_latest_price()
    if db_data:
        return jsonify(db_data)
    
    # Fall back to in-memory data if DynamoDB fails
    if latest_stocks.empty():
        return jsonify({'error': 'No data available'}), 404
    return jsonify(latest_stocks.queue[0])

@app.route('/api/stock/history', methods=['GET'])
def get_stock_history():
    try:
        # Get the last 7 days of data
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=7)).isoformat()
        
        history = db_manager.get_price_history(start_date, end_date)
        return jsonify({'data': history})
    except Exception as e:
        logger.error(f"Error fetching price history: {e}")
        return jsonify({'error': 'Failed to fetch price history'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'kafka_queue_size': latest_stocks.qsize()
    })

def start_app():
    try:
        # Start Kafka listener thread
        kafka_listener = KafkaListener()
        kafka_listener.start()
        
        # Start Flask app
        app.run(host='0.0.0.0', port=5002, debug=False)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        raise

if __name__ == '__main__':
    start_app()
