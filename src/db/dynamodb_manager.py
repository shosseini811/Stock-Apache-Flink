import boto3
from botocore.exceptions import ClientError
import time
from datetime import datetime
import logging
import os
from decimal import Decimal

logger = logging.getLogger(__name__)

class DynamoDBManager:
    def __init__(self, table_name='bitcoin_prices'):
        self.table_name = table_name
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-1',  # Change this to your preferred region
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
        
        # Get table if exists, create if it doesn't
        self.table = self._get_or_create_table()

    def _get_or_create_table(self):
        try:
            table = self.dynamodb.Table(self.table_name)
            table.load()
            return table
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create table
                table = self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'date',
                            'KeyType': 'HASH'  # Partition key
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'  # Sort key
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'date',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'AttributeType': 'S'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'  # On-demand pricing
                )
                
                # Wait for table creation
                table.meta.client.get_waiter('table_exists').wait(
                    TableName=self.table_name
                )
                return table
            else:
                logger.error(f"Error accessing DynamoDB: {e}")
                raise

    def _float_to_decimal(self, value):
        """Convert float to Decimal for DynamoDB"""
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    def save_price(self, price_data):
        """
        Save Bitcoin price data to DynamoDB
        
        price_data should contain:
        - price: float
        - change: float
        - change_percent: str
        - timestamp: str (ISO format)
        """
        try:
            timestamp = datetime.fromisoformat(price_data['timestamp'])
            date = timestamp.date().isoformat()
            
            # Convert float values to Decimal
            item = {
                'date': date,
                'timestamp': timestamp.isoformat(),
                'price': self._float_to_decimal(price_data['price']),
                'change': self._float_to_decimal(price_data['change']),
                'change_percent': price_data['change_percent']
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Saved price data for {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving price data: {e}")
            return False

    def get_latest_price(self):
        """Get the most recent Bitcoin price"""
        try:
            date = datetime.now().date().isoformat()
            response = self.table.query(
                KeyConditionExpression='#date = :date',
                ExpressionAttributeNames={'#date': 'date'},
                ExpressionAttributeValues={':date': date},
                ScanIndexForward=False,  # Sort descending
                Limit=1
            )
            
            if response['Items']:
                # Convert Decimal back to float for JSON serialization
                item = response['Items'][0]
                item['price'] = float(item['price'])
                item['change'] = float(item['change'])
                return item
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest price: {e}")
            return None

    def get_price_history(self, start_date, end_date=None):
        """Get Bitcoin price history between dates"""
        try:
            if end_date is None:
                end_date = datetime.now().date().isoformat()
                
            response = self.table.query(
                KeyConditionExpression='#date BETWEEN :start_date AND :end_date',
                ExpressionAttributeNames={'#date': 'date'},
                ExpressionAttributeValues={
                    ':start_date': start_date,
                    ':end_date': end_date
                }
            )
            
            # Convert Decimal to float for JSON serialization
            items = response['Items']
            for item in items:
                item['price'] = float(item['price'])
                item['change'] = float(item['change'])
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return []
