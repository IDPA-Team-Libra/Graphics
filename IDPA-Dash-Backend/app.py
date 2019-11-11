# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 23:22:31 2019

@author: Janis Tejero
"""

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas_datareader.data as web
import datetime as dt
import requests


def get_symbol(symbol):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)

    result = requests.get(url).json()

    for x in result['ResultSet']['Result']:
        if x['symbol'] == symbol:
            return x['name']
    
app = dash.Dash(__name__)

server = app.server

app.config['suppress_callback_exceptions'] = True
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
                dcc.DatePickerRange(
                        id = 'date-picker',
                        min_date_allowed = dt.datetime(2005, 1, 1),
                        max_date_allowed = dt.datetime.now(),
                        initial_visible_month = dt.datetime(2019, 1, 1),
                        end_date = dt.datetime(2019, 1, 1)
                        )
            ]),
        html.Div(id='output-graph'),    
], style={'marginBottom': 100, 'marginTop': 100})        



@app.callback(
    Output(component_id='output-graph', component_property='children'),
    [Input(component_id='input', component_property='value'),
     Input(component_id='theme-color', component_property='value'),
     Input(component_id='date-picker', component_property='start_date'),
     Input(component_id='date-picker', component_property='end_date')])


    
def update_graph(stock, theme, start_date, end_date):

    #start = dt.datetime(2010, 1, 1)
    #end = dt.datetime.now()
    df = web.DataReader(stock, 'yahoo', start_date, end_date)
   
    company = get_symbol(stock)
    
    # set theme
    theme_color = ''
    text_color = ''
    if theme == 'Dark':
        theme_color = '#46464a'
        text_color = '#f7f7f7'
    elif theme == 'Bright':
        theme_color == '#f7f7f7'
        text_color = '#2b2b2b'
        
    return dcc.Graph(
            id='example-graph',
            figure={
                'data': [
                    {'x': df.index, 'y': df.Close, 'type' : 'line', 'name': stock},
                ],
                'layout': {
                    'title': stock + '   (' + company + ')',
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
    app.run_server(debug=True)
