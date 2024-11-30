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

    def add_point(self, price, timestamp, change):
        self.prices.append(price)
        self.timestamps.append(timestamp)
        self.changes.append(change)
        
        # Keep only the last max_points
        if len(self.prices) > self.max_points:
            self.prices.pop(0)
            self.timestamps.pop(0)
            self.changes.pop(0)

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
    
    # Update data store
    price = data['price']
    timestamp = datetime.fromisoformat(data['timestamp'])
    change = float(data['change'])
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
        mode='lines',
        name='Price',
        line=dict(color='#3498db', width=2),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.1)'
    ))
    
    # Update layout
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(189, 195, 199, 0.2)',
            title='Time'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(189, 195, 199, 0.2)',
            title='Price (USD)',
            tickformat='$,.2f'
        ),
        hovermode='x unified'
    )
    
    return (
        f"${price:,.2f}",
        price_style,
        f"{'+' if change >= 0 else ''}{change:,.2f} ({data['change_percent']}%)",
        change_style,
        fig
    )

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
