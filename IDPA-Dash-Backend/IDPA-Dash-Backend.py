# -*- coding: utf-8 -*-
"""
Created on Sat Nov  9 10:39:34 2019

@author: Janis Tejero
"""

import os
import dash
import pandas as pd
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas_datareader.data as web
import datetime as dt
import requests
import urllib
import json
from pandas.io.json import json_normalize


os.environ['ALPHAVANTAGE_API_KEY'] = 'S7QOYZV61QZ7Z3LM'
#url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=AAPL&interval=60min&outputsize=full&apikey=S7QOYZV61QZ7Z3LM"


def getResponse(url):
    operUrl = urllib.request.urlopen(url)
    if(operUrl.getcode()==200):
       data = operUrl.read()
    else:
       print("Error receiving data", operUrl.getcode())
    return data


def get_symbol(symbol):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
    result = requests.get(url).json()

    for x in result['ResultSet']['Result']:
        if x['symbol'] == symbol:
            return x['name']
    
app = dash.Dash()
app.config['suppress_callback_exceptions'] = True

server = app.server

app.layout = html.Div(children=[
        html.Div(children='''
            Stock Ticker:
            '''),
        html.Div([
                dcc.Input(id = 'input', value = '', type = 'text'), 
                dcc.RadioItems(
                        id = 'theme-color',
                        options = [{'label': i, 'value': i} for i in ['Bright', 'Dark']],
                        value = 'Bright',
                        labelStyle = {'display' : 'inline-block'}
                        ),
                dcc.Dropdown(
                        id='interval-picker',
                        className = 'interval-picker',
                        options=[
                        {'label': '1min', 'value': '1min'},
                        {'label': '5min', 'value': '5min'},
                        {'label': '15min', 'value': '15min'},
                        {'label': '30min', 'value': '30min'},
                        {'label': '60min', 'value': '60min'}],
                        ),
                dcc.DatePickerRange(
                        id = 'date-picker',
                        min_date_allowed = dt.datetime(2010, 1, 1),
                        max_date_allowed = dt.datetime.now(),
                        initial_visible_month = dt.datetime(2019, 1, 1),
                        end_date = dt.datetime.now()
                        )
            ]),
        html.Div(id='output-graph'),    
], style={'marginBottom': 100, 'marginTop': 100})        

def intraday_alpha_vantage(symbol, timeframe):
    data = getResponse("https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol="+symbol+"&interval="+timeframe+"&outputsize=full&apikey=S7QOYZV61QZ7Z3LM")
    parsed = json.loads(data)
    json_normalize(parsed)
    
    del parsed["Meta Data"]
    parsed = parsed['Time Series ('+timeframe+')'] 
    
    df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    for d,p in parsed.items():
        date = dt.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
        data_row = [date, float(p['1. open']), float(p['2. high']), float(p['3. low']), float(p['4. close']), int(p['5. volume'])]
        df.loc[-1,:] = data_row
        df.index = df.index + 1
    df = df.sort_values('date')
    df.iloc[::-1]
    
    return df

def daily_alpha_vantage(symbol):
    data = getResponse("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol="+symbol+"&outputsize=full&apikey=S7QOYZV61QZ7Z3LM")
    parsed = json.loads(data)
    json_normalize(parsed)
    
    del parsed["Meta Data"]
    parsed = parsed['Time Series (Daily)'] 
    
    df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    for d,p in parsed.items():
        date = dt.datetime.strptime(d, '%Y-%m-%d')
        data_row = [date, float(p['1. open']), float(p['2. high']), float(p['3. low']), float(p['4. close']), int(p['5. volume'])]
        df.loc[-1,:] = data_row
        df.index = df.index + 1
    df = df.sort_values('date')
    df.iloc[::-1]
    
    return df

def daily(symbol, start_date, end_date):    
    df = web.DataReader(symbol, 'av-daily', start_date, end_date, api_key=os.getenv('ALPHAVANTAGE_API_KEY'))
    return df

def weekly_alpha_vantage(symbol):
    data = getResponse("https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol="+symbol+"&outputsize=full&apikey=S7QOYZV61QZ7Z3LM")
    parsed = json.loads(data)
    json_normalize(parsed)
    
    del parsed["Meta Data"]
    parsed = parsed['Time Series (Daily)'] 
    
    df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    for d,p in parsed.items():
        date = dt.datetime.strptime(d, '%Y-%m-%d')
        data_row = [date, float(p['1. open']), float(p['2. high']), float(p['3. low']), float(p['4. close']), int(p['5. volume'])]
        df.loc[-1,:] = data_row
        df.index = df.index + 1
    df = df.sort_values('date')
    df.iloc[::-1]
    
    return df

@app.callback(
    Output(component_id='output-graph', component_property='children'),
    [Input(component_id='input', component_property='value'),
     Input(component_id='theme-color', component_property='value'),
     Input(component_id='date-picker', component_property='start_date'),
     Input(component_id='date-picker', component_property='end_date'),
     Input(component_id='interval-picker', component_property='value')])

def update_graph(symbol, theme, start_date, end_date, interval):

    #df = web.DataReader(stock, 'yahoo', start_date, end_date)
    #df = web.DataReader(symbol, "av-daily", start_date, end_date, api_key=os.getenv('ALPHAVANTAGE_API_KEY'))
    
    if start_date is None:
        start_date = dt.datetime(2010, 1, 1)
    if end_date is None:
        end_date = dt.datetime.now()
    
    # set theme
    theme_color = ''
    text_color = ''
    if theme == 'Dark':
        theme_color = '#46464a'
        text_color = '#f7f7f7'
    elif theme == 'Bright':
        theme_color == '#f7f7f7'
        text_color = '#2b2b2b'
        
        
    changeAPI = False
    if interval is None:
        df = daily(symbol, start_date, end_date)
        changeAPI = True
    else:
        df = intraday_alpha_vantage(symbol, interval)
        
        
    company = get_symbol(symbol)
        
    if changeAPI is True:
        graph_data = {'x': df.index, 'y': df.close, 'type' : 'line', 'name': symbol}
    else:
        graph_data = {'x': df.date, 'y': df.close, 'type' : 'line', 'name': symbol}
    return dcc.Graph(
            id='example-graph',
            figure={
                'data': [
                   graph_data,
                ],
                'layout': {
                    'title': symbol + '   (' + company + ')',
                    'paper_bgcolor' : theme_color,
                    'plot_bgcolor': theme_color,
                    'xaxis' : dict(
                            showgrid = True,
                            title = 'Time',
                            color = text_color
                    ),
                    'yaxis' : dict(
                            showgrid = True,
                            title = 'Price',
                            color = text_color
                    ),
                    'font': {
                        'color' : text_color
                    },
                    
                }
            }
    )

        
if __name__ == '__main__':
    app.run_server(debug=False, use_reloader=False)
