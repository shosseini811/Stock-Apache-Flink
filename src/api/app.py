from flask import Flask, jsonify, request
import boto3
import json
import logging
from threading import Thread
import queue
from datetime import datetime, timedelta
import os
import sys
import time

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.dynamodb_manager import DynamoDBManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize DynamoDB manager
db_manager = DynamoDBManager()

# In-memory cache for latest stock data
latest_stocks = queue.Queue(maxsize=100)

class KinesisListener(Thread):
    def __init__(self, stream_name='stock-data-stream', region='us-west-2'):
        Thread.__init__(self)
        self.stream_name = stream_name
        self.region = region
        self.daemon = True  # Thread will exit when main program exits
        
    def run(self):
        try:
            # Initialize Kinesis client
            kinesis_client = boto3.client('kinesis', region_name=self.region)
            
            # Get shard iterator
            response = kinesis_client.describe_stream(StreamName=self.stream_name)
            shard_id = response['StreamDescription']['Shards'][0]['ShardId']
            
            iterator_response = kinesis_client.get_shard_iterator(
                StreamName=self.stream_name,
                ShardId=shard_id,
                ShardIteratorType='LATEST'
            )
            shard_iterator = iterator_response['ShardIterator']
            
            logger.info(f"Started listening to Kinesis stream: {self.stream_name}")
            
            while True:
                try:
                    # Get records from the shard
                    response = kinesis_client.get_records(
                        ShardIterator=shard_iterator,
                        Limit=100
                    )
                    
                    # Process records
                    for record in response['Records']:
                        try:
                            data = json.loads(record['Data'].decode('utf-8'))
                            # Update the latest stocks queue
                            if latest_stocks.full():
                                latest_stocks.get()  # Remove oldest item if queue is full
                            latest_stocks.put(data)
                            logger.debug(f"Processed record: {data}")
                            # Save data to DynamoDB
                            db_manager.save_price(data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Error decoding JSON: {e}")
                        except Exception as e:
                            logger.error(f"Error processing record: {e}")
                    
                    # Update shard iterator
                    shard_iterator = response['NextShardIterator']
                    
                    # Add a small delay to avoid excessive API calls
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error getting records: {e}")
                    time.sleep(5)  # Wait before retrying
                    
        except Exception as e:
            logger.error(f"Error in Kinesis listener: {e}")

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
        'kinesis_queue_size': latest_stocks.qsize()
    })

def start_app():
    # Start Kinesis listener thread
    listener = KinesisListener()
    listener.start()
    logger.info("Started Kinesis listener thread")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    start_app()
