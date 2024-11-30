# Real-Time Stock Dashboard

A real-time stock data processing and visualization system built with Apache Flink, Kafka, Flask, and Plotly Dash.

## Features
- Real-time stock data scraping from Yahoo Finance
- Stream processing with Apache Flink
- Real-time data visualization with Plotly Dash
- RESTful API with Flask
- Message queuing with Apache Kafka

## Project Structure
```
Stock-Apache-Flink/
├── src/
│   ├── scraper/
│   │   └── stock_scraper.py
│   ├── processing/
│   │   └── flink_processor.py
│   ├── api/
│   │   └── app.py
│   └── dashboard/
│       └── dashboard.py
├── requirements.txt
├── venv/
└── README.md
```

## Setup Instructions

1. Create and activate virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start Kafka and create required topics:
```bash
# Start Kafka (ensure Zookeeper is running)
kafka-topics --create --topic stock_data --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
kafka-topics --create --topic processed_stock_data --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

4. Start the components in separate terminals:
```bash
# Make sure virtual environment is activated in each terminal
source venv/bin/activate  # On macOS/Linux
# .\venv\Scripts\activate  # On Windows

# Terminal 1: Start the scraper
python src/scraper/stock_scraper.py

# Terminal 2: Start the Flink processor
python src/processing/flink_processor.py

# Terminal 3: Start the Flask API
python src/api/app.py

# Terminal 4: Start the dashboard
python src/dashboard/dashboard.py
```

5. Access the dashboard at http://localhost:8050

## Requirements
- Python 3.8+
- Apache Kafka
- Apache Flink
- Web browser for dashboard visualization

## Deactivating Virtual Environment
When you're done working on the project, you can deactivate the virtual environment:
```bash
deactivate