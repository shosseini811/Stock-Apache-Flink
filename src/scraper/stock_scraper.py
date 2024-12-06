import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import boto3
import logging
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

def delivery_report(err, msg):
    if err is not None:
        logger.error(f'Message delivery failed: {err}')
    else:
        logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')

class BitcoinScraper:
    def __init__(self, stream_name='stock-data-stream', region='us-west-2'):
        # Initialize AWS Kinesis client
        self.kinesis_client = boto3.client('kinesis', region_name=region)
        self.stream_name = stream_name
        self.url = "https://finance.yahoo.com/quote/BTC-USD/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        # Initialize DynamoDB manager
        self.db_manager = DynamoDBManager()

    def get_bitcoin_price(self):
        try:
            # Fetch the webpage
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the price element
            price_element = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
            if not price_element:
                logger.error("Could not find Bitcoin price")
                return None

            # Get price and clean it
            price = float(price_element.text.replace(',', ''))
            
            # Get additional information
            change_element = soup.find('fin-streamer', {'data-field': 'regularMarketChange'})
            change_percent_element = soup.find('fin-streamer', {'data-field': 'regularMarketChangePercent'})
            
            change = float(change_element.text.replace(',', '')) if change_element else 0
            change_percent = change_percent_element.text.strip('()%') if change_percent_element else '0'
            
            bitcoin_data = {
                "symbol": "BTC-USD",
                "price": price,
                "change": change,
                "change_percent": change_percent,
                "timestamp": datetime.now().isoformat()
            }
            
            return bitcoin_data

        except requests.RequestException as e:
            logger.error(f"Error fetching data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def send_to_kinesis(self, data):
        try:
            response = self.kinesis_client.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(data),
                PartitionKey=data['symbol']
            )
            logger.info(f"Data sent to Kinesis. Sequence number: {response['SequenceNumber']}")
        except Exception as e:
            logger.error(f"Error sending data to Kinesis: {str(e)}")

    def save_to_db(self, data):
        """Save price data to DynamoDB"""
        if data:
            success = self.db_manager.save_price(data)
            if success:
                logger.info(f"Saved to DynamoDB - Bitcoin Price: ${data['price']:,.2f}")
            else:
                logger.error("Failed to save to DynamoDB")

    def run(self, interval_seconds=10):
        logger.info("Starting Bitcoin price scraper...")
        while True:
            try:
                bitcoin_data = self.get_bitcoin_price()
                
                if bitcoin_data:
                    # Send to Kinesis
                    self.send_to_kinesis(bitcoin_data)
                    
                    # Save to DynamoDB
                    self.save_to_db(bitcoin_data)
                    
                    # Log the data
                    logger.info("-" * 50)
                    logger.info(f"Price: ${bitcoin_data['price']:,.2f}")
                    logger.info(f"Change: ${bitcoin_data['change']:.2f}")
                    logger.info(f"Change %: {bitcoin_data['change_percent']}%")
                    logger.info("-" * 50)
                else:
                    logger.warning("Failed to retrieve Bitcoin price")
                
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Stopping Bitcoin price scraper...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(interval_seconds)

if __name__ == "__main__":
    scraper = BitcoinScraper()
    scraper.run()
