import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Dash app with a clean, modern theme
app = dash.Dash(
    __name__,
    title='Bitcoin Price Dashboard',
    update_title=None
)

# Store for historical data
class DataStore:
    def __init__(self, max_points=100):
        self.max_points = max_points
        self.prices = []
        self.timestamps = []
        self.changes = []
        self.last_update = None

    def add_point(self, price, timestamp, change):
        try:
            # Convert string timestamp to datetime if needed
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Only add if timestamp is newer than last update
            if not self.last_update or timestamp > self.last_update:
                self.prices.append(float(price))
                self.timestamps.append(timestamp)
                self.changes.append(float(change))
                self.last_update = timestamp
                
                # Keep only the last max_points
                if len(self.prices) > self.max_points:
                    self.prices.pop(0)
                    self.timestamps.pop(0)
                    self.changes.pop(0)
                return True
        except Exception as e:
            logger.error(f"Error adding data point: {e}")
        return False

data_store = DataStore()

# Define the layout with a modern, clean design
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Bitcoin Real-Time Price Dashboard", 
                style={'color': '#2c3e50', 'marginBottom': 10}),
        html.P("Live updates every 5 seconds",
               style={'color': '#7f8c8d'})
    ], style={'textAlign': 'center', 'padding': '20px'}),
    
    # Main content
    html.Div([
        # Current Price Card
        html.Div([
            html.H3("Current Price", style={'color': '#34495e', 'marginBottom': 10}),
            html.Div(id='current-price', style={'fontSize': '2.5em', 'fontWeight': 'bold'})
        ], className='price-card'),
        
        # Price Change Card
        html.Div([
            html.H3("24h Change", style={'color': '#34495e', 'marginBottom': 10}),
            html.Div(id='price-change', style={'fontSize': '2em'})
        ], className='price-card'),
        
        # Price Chart
        html.Div([
            html.H3("Price History", style={'color': '#34495e', 'marginBottom': 20}),
            dcc.Graph(id='price-chart')
        ], style={'marginTop': 30}),
        
    ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'}),
    
    # Update interval
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # Update every 5 seconds
        n_intervals=0
    )
], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh'})

def fetch_bitcoin_data():
    try:
        response = requests.get('http://localhost:5002/api/stock/latest')
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching data: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching bitcoin data: {e}")
        return None

@app.callback(
    [Output('current-price', 'children'),
     Output('current-price', 'style'),
     Output('price-change', 'children'),
     Output('price-change', 'style'),
     Output('price-chart', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    data = fetch_bitcoin_data()
    
    if not data:
        return "N/A", {}, "N/A", {}, {}
    
    try:
        # Update data store
        price = float(data['price'])
        timestamp = data['timestamp']
        change = float(data.get('change', 0))
        data_store.add_point(price, timestamp, change)
        
        # Format current price
        price_style = {
            'fontSize': '2.5em',
            'fontWeight': 'bold',
            'color': '#2c3e50'
        }
        
        # Format price change
        change_color = '#2ecc71' if change >= 0 else '#e74c3c'
        change_style = {
            'fontSize': '2em',
            'color': change_color
        }
        
        # Create price chart
        fig = go.Figure()
        
        # Add price line
        fig.add_trace(go.Scatter(
            x=data_store.timestamps,
            y=data_store.prices,
            mode='lines+markers',
            name='Price',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.1)'
        ))
        
        # Calculate time range for x-axis
        if data_store.timestamps:
            x_min = min(data_store.timestamps)
            x_max = max(data_store.timestamps)
            # Add some padding
            x_range = [
                x_min - timedelta(minutes=1),
                x_max + timedelta(minutes=1)
            ]
        else:
            x_range = None
        
        # Update layout
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=40, r=40, t=20, b=40),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(189, 195, 199, 0.2)',
                title='Time',
                range=x_range,
                tickformat='%H:%M:%S'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(189, 195, 199, 0.2)',
                title='Price (USD)',
                tickformat='$,.2f'
            ),
            hovermode='x unified',
            showlegend=False
        )
        
        change_percent = data.get('change_percent', '0.00')
        if isinstance(change_percent, str):
            change_percent = change_percent.replace('%', '')
        change_percent = float(change_percent)
        
        return (
            f"${price:,.2f}",
            price_style,
            f"{'+' if change >= 0 else ''}{change:,.2f} ({change_percent:,.2f}%)",
            change_style,
            fig
        )
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        return "Error", {}, "Error", {}, {}

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
