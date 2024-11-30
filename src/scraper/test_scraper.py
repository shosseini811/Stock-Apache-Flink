import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

def scrape_bitcoin_price():
    url = "https://finance.yahoo.com/quote/BTC-USD/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        # Fetch the webpage
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the price element (using the fin-streamer tag with data-field="regularMarketPrice")
        price_element = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
        if not price_element:
            print("Could not find Bitcoin price")
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
        print(f"Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def main():
    print("\nStarting Bitcoin price scraper...")
    while True:
        try:
            bitcoin_data = scrape_bitcoin_price()
            
            if bitcoin_data:
                print("\nBitcoin Price Data:")
                print("-" * 50)
                print(f"Price: ${bitcoin_data['price']:,.2f}")
                print(f"Change: ${bitcoin_data['change']:.2f}")
                print(f"Change %: {bitcoin_data['change_percent']}%")
                print(f"Time: {bitcoin_data['timestamp']}")
                print("-" * 50)
            else:
                print("Failed to retrieve Bitcoin price")
            
            # Wait before next scrape
            print("\nWaiting 10 seconds before next update...")
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\nScraping stopped by user")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
