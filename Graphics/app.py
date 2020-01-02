# -*- coding: utf-8 -*-
"""
Created on Sat Nov  9 10:39:34 2019

@author: Janis Tejero
"""

import os
import dash
import pandas as pd
import requests
import urllib
import json

import dash_core_components as dcc
import dash_html_components as html
import pandas_datareader.data as web
import datetime as dt
import plotly.graph_objs as go

from dash.dependencies import Input, Output
from pandas.io.json import json_normalize

os.environ['ALPHAVANTAGE_API_KEY'] = 'S7QOYZV61QZ7Z3LM'

urlinput = 'AAPL'


def getResponse(url):
    operUrl = requests.get(url)
    return operUrl.content


def get_symbol(symbol):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(
        symbol)
    result = requests.get(url).json()

    for x in result['ResultSet']['Result']:
        if x['symbol'] == symbol:
            return x['name']


app = dash.Dash(__name__)
app.config['suppress_callback_exceptions'] = True

server = app.server


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        dcc.RadioItems(
            id='theme-color',
            className='inline input-field',
            options=[{'label': i, 'value': i} for i in ['Bright', 'Dark']],
            value='Bright',
            labelStyle={'display': 'inline-block'}
        ),
        dcc.RadioItems(
            id='type-radio',
            className='inline input-field',
            options=[{'label': i, 'value': i}
                     for i in ['Line', 'Candlestick']],
            value='Line',
            labelStyle={'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='interval-picker',
            className='interval-picker',
            options=[
                {'label': '1min', 'value': '1'},
                {'label': '5min', 'value': '5'},
                {'label': '15min', 'value': '15'},
                {'label': '30min', 'value': '30'},
                {'label': '60min', 'value': '60'},
                {'label': '1D', 'value': '1D'},
                {'label': 'Weekly', 'value': '1W'},
                {'label': 'Monthly', 'value': '1M'},
            ],
            value='1D',
            style={'display': 'inline-block'}
        ),
    ], className=''),
    html.Div(id='page-content'),
    dcc.Graph(id='output-graph')
], style={'marginBottom': 100, 'marginTop': 100}, className='raleway-font input-section')


def intraday_alpha_vantage(symbol, timeframe):
    data = getResponse(
        "http://0.0.0.0:3440/stock/{}/{}".format(symbol, timeframe))
    parsed = json.loads(data)
    df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    timeseries = []
    for entry in parsed:
        date = dt.datetime.strptime(entry["Time"], '%Y-%m-%dT%H:%M:%SZ')
        data_row = [float(entry['Open']), float(entry['High']), float(
            entry['Low']), float(entry['Close']), int(entry['Volume'])]
        df.loc[-1, :] = data_row
        timeseries.append(date)
        df.index = df.index + 1
    df.iloc[::-1]
    datetime_series = pd.to_datetime(timeseries)
    datetime_index = pd.DatetimeIndex(datetime_series.values)
    df = df.set_index(datetime_index)
    return df


def daily(symbol):
    data = getResponse("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=" +
                       symbol+"&outputsize=full&apikey=S7QOYZV61QZ7Z3LM")
    parsed = json.loads(data)
    json_normalize(parsed)

    parsed = parsed['Time Series (Daily)']
    df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    timeseries = []
    for d, p in parsed.items():
        date = dt.datetime.strptime(d, '%Y-%m-%d')
        data_row = [float(p['1. open']), float(p['2. high']), float(
            p['3. low']), float(p['4. close']), int(p['5. volume'])]
        df.loc[-1, :] = data_row
        timeseries.append(date)
        df.index = df.index + 1
    df.iloc[::-1]

    datetime_series = pd.to_datetime(timeseries)
    datetime_index = pd.DatetimeIndex(datetime_series.values)
    df = df.set_index(datetime_index)
    return df


@app.callback(
    Output(component_id='output-graph', component_property='figure'),
    [Input(component_id='theme-color', component_property='value'),
     Input(component_id='interval-picker', component_property='value'),
     Input(component_id='type-radio', component_property='value'),
     Input(component_id='url', component_property='pathname')])
def update_graph(theme, interval, chart_type, urlinput):

    if urlinput is None:
        urlinput = 'AAPL'
    else:
        urlinput = urlinput[1:]
    # set theme
    theme_color = '#f7f7f7'
    text_color = '#2b2b2b'
    grid_color = '#E4E4E4'
    line_color = '#5E0DAC'
    if theme == 'Dark':
        theme_color = '#262a30'
        text_color = '#f7f7f7'
        grid_color = '#393D42'
        line_color = '#ffffff'
    elif theme == 'Bright':
        theme_color = '#f7f7f7'
        text_color = '#2b2b2b'
        line_color = '#5E0DAC'

    if interval == '1D':
        df = daily(urlinput)
    else:
        df = intraday_alpha_vantage(urlinput, interval)

    company = get_symbol(urlinput)

    if chart_type == 'Candlestick':
        figure = go.Figure(data=[go.Candlestick(x=df.index,
                                                open=df.open,
                                                high=df.high,
                                                low=df.low,
                                                close=df.close)])

        figure.update_layout(xaxis_rangeslider_visible=False, plot_bgcolor=theme_color,
                             paper_bgcolor=theme_color, font_color=text_color, title='Stock Prices for ' +
                             company + ' over Time',
                             title_x=0.5)
        figure.update_xaxes(gridcolor=grid_color)
        figure.update_yaxes(gridcolor=grid_color)

        return figure

    elif chart_type == 'Line':
        line_trace = []
        line_trace.append(go.Scatter(x=df.index, y=df.close))

        figure = {'data': line_trace,
                  'layout': go.Layout(
                      colorway=[line_color, '#FF4F00', '#375CB1',
                                '#FF7400', '#FFF400', '#FF0056'],
                      title='Stock Prices for ' + company + ' over Time',
                      xaxis={'title': 'Time',
                             'rangeselector': {'buttons': list([
                                 {'count': 1, 'label': '1D',
                                  'step': 'day', 'stepmode': 'backward'},
                                 {'count': 7, 'label': '1W',
                                  'step': 'day', 'stepmode': 'backward'},
                                 {'count': 1, 'label': '1M',
                                  'step': 'month', 'stepmode': 'backward'},
                                 {'count': 6, 'label': '6M',
                                  'step': 'month', 'stepmode': 'backward'},
                                 {'count': 1, 'label': '1Y',
                                  'step': 'year', 'stepmode': 'backward'},
                                 {'step': 'all'}])}, 'color': text_color},
                      yaxis={'title': 'Price (USD)', 'color': text_color},
                      font={'color': text_color},
                      plot_bgcolor=theme_color,
                      paper_bgcolor=theme_color)
                  }
        return figure


if __name__ == '__main__':
    app.run_server(debug=False, use_reloader=False)
