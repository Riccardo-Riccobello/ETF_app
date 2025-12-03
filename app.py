
import pandas as pd
import numpy as np
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from datetime import datetime
import dash_bootstrap_components as dbc
import os

# Alpaca API credentials
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")


# Initialize Alpaca client
client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

# ETF options
ETF_OPTIONS = {
    "VT": "Vanguard Total World Stock ETF",
    "ACWI": "iShares MSCI ACWI ETF",
    "URTH": "iShares MSCI World ETF",
    "SPGM": "SPDR Portfolio MSCI Global Stock Market ETF"
}

DEFAULT_INVESTMENT = 585.0
DEFAULT_START_DATE = "2025-01-01"

# Fetch ETF data
def fetch_etf_data(symbol, start_date):
    request_params = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=datetime.strptime(start_date, "%Y-%m-%d"),
        end=datetime.now(),
        feed='iex'
    )
    bars = client.get_stock_bars(request_params)
    data = bars.df.reset_index()
    data.rename(columns={'timestamp': 'Date', 'close': 'Close'}, inplace=True)
    return data[['Date', 'Close']]

# Simulate returns
def simulate_returns(data, initial_investment):
    start_price = data['Close'].iloc[0]
    data['Value'] = initial_investment * (data['Close'] / start_price)
    return data

# Calculate performance metrics
def calculate_metrics(data):
    total_return = (data['Value'].iloc[-1] / data['Value'].iloc[0] - 1) * 100
    days = (data['Date'].iloc[-1] - data['Date'].iloc[0]).days
    years = days / 365
    cagr = ((data['Value'].iloc[-1] / data['Value'].iloc[0]) ** (1 / years) - 1) * 100
    daily_returns = data['Close'].pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252) * 100
    cumulative = (1 + daily_returns).cumprod()
    max_drawdown = ((cumulative / cumulative.cummax()) - 1).min() * 100
    return {
        "Total Return (%)": round(total_return, 2),
        "CAGR (%)": round(cagr, 2),
        "Volatility (%)": round(volatility, 2),
        "Max Drawdown (%)": round(max_drawdown, 2)
    }

# Dash app with Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "ETF Investment Simulator"

app.layout = dbc.Container([
    html.H2("🌍 Global ETF Investment Simulator", className="text-center mt-4 mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label("Select ETF:", className="fw-bold"),
                    dcc.Dropdown(
                        id='etf-symbol',
                        options=[{"label": name, "value": symbol} for symbol, name in ETF_OPTIONS.items()],
                        value="VT",
                        className="mb-3"
                    ),
                    
                    html.Label("Start Date (YYYY-MM-DD):", className="fw-bold"),
                    dbc.Input(id='start-date', type='text', value=DEFAULT_START_DATE, className="mb-3"),
                    
                    html.Label("Initial Investment ($):", className="fw-bold"),
                    dbc.Input(id='investment', type='number', value=DEFAULT_INVESTMENT, className="mb-3"),
                    
                    dbc.Button("Simulate", id='simulate-button', color="primary", className="w-100")
                ])
            ], className="shadow-sm")
        ], width=4),
        
        dbc.Col([
            dcc.Graph(id='simulation-chart', style={"height": "60vh"}),
            html.Div(id='metrics-output', className="mt-4")
        ], width=8)
    ], className="mt-4")
], fluid=True)

@app.callback(
    [Output('simulation-chart', 'figure'),
     Output('metrics-output', 'children')],
    Input('simulate-button', 'n_clicks'),
    [dash.dependencies.State('etf-symbol', 'value'),
     dash.dependencies.State('start-date', 'value'),
     dash.dependencies.State('investment', 'value')]
)
def update_chart(n_clicks, etf_symbol, start_date, investment):
    if n_clicks == 0:
        return px.line(title="Simulation will appear here"), ""
    
    # Fetch data
    data = fetch_etf_data(etf_symbol, start_date)
    
    # Simulate returns
    simulated_data = simulate_returns(data, investment)
    
    # Calculate metrics
    metrics = calculate_metrics(simulated_data)
    
    # Create chart
    fig = px.line(simulated_data, x='Date', y='Value',
                  title=f'{ETF_OPTIONS[etf_symbol]} Simulation (USD)',
                  labels={'Value': 'Portfolio Value ($)'})
    fig.update_layout(template="plotly_white", font=dict(size=14))
    
    # Metrics display
    metrics_table = dbc.Table([
        html.Thead(html.Tr([html.Th("Metric"), html.Th("Value")])),
        html.Tbody([html.Tr([html.Td(k), html.Td(f"{v}%")]) for k, v in metrics.items()])
    ], bordered=True, hover=True, responsive=True, className="mt-3")
    
    return fig, metrics_table

if __name__ == '__main__':
    app.run(debug=True)

