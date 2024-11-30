import boto3
from decimal import Decimal
from datetime import datetime, timedelta
import json
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_table():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    return dynamodb.Table('bitcoin_prices')

def print_results(items):
    """Pretty print the results"""
    for item in items:
        print(json.dumps(item, indent=2, cls=DecimalEncoder))

def get_latest_price():
    """Get the most recent Bitcoin price"""
    table = get_table()
    date = datetime.now().date().isoformat()
    
    response = table.query(
        KeyConditionExpression='#date = :date',
        ExpressionAttributeNames={'#date': 'date'},
        ExpressionAttributeValues={':date': date},
        ScanIndexForward=False,  # Sort descending
        Limit=1
    )
    
    if response['Items']:
        print("\nLatest price:")
        print_results(response['Items'])
    else:
        print("No prices found for today")

def get_prices_for_date(date_str):
    """Get all prices for a specific date"""
    table = get_table()
    
    response = table.query(
        KeyConditionExpression='#date = :date',
        ExpressionAttributeNames={'#date': 'date'},
        ExpressionAttributeValues={':date': date_str},
        ScanIndexForward=True  # Sort ascending by timestamp
    )
    
    print(f"\nPrices for {date_str}:")
    print_results(response['Items'])

def get_price_history(start_date, end_date=None):
    """Get price history between dates"""
    if end_date is None:
        end_date = datetime.now().date().isoformat()
    
    table = get_table()
    response = table.query(
        KeyConditionExpression='#date BETWEEN :start_date AND :end_date',
        ExpressionAttributeNames={'#date': 'date'},
        ExpressionAttributeValues={
            ':start_date': start_date,
            ':end_date': end_date
        }
    )
    
    print(f"\nPrice history from {start_date} to {end_date}:")
    print_results(response['Items'])

if __name__ == "__main__":
    # Get latest price
    get_latest_price()
    
    # Get prices for today
    today = datetime.now().date().isoformat()
    get_prices_for_date(today)
    
    # Get prices for the last 7 days
    week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
    get_price_history(week_ago)
