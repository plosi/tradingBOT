import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
from dash.dependencies import Input, Output

import pandas as pd
import datetime

# from tradingbot import datafile, walletfile
datafile = "data/btc_trend.csv" 	# make sure that folder data exists
walletfile = "data/bal.csv"		# make sure that folder data exists

# make an instance of Dash
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.MINTY],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

app.layout = dbc.Container([
        html.H1('BTC trend graph'),
        dcc.Graph(id='BTC_graph'),
        dcc.Graph(id='MACD_graph'),
        html.Div(id='table'),
        dcc.Interval(
            id='timer',
            interval=60*1000, # in millis
            n_intervals=0
        )
])

@app.callback([Output('BTC_graph', 'figure'),
            Output('MACD_graph', 'figure')],
            Output('table', 'children'),
            [Input('timer', 'n_intervals')])
def update_dashboard(n):  

    # open the dataframe
    df = pd.read_csv(datafile)
    # get the the last transaction details and balance
    with open(walletfile, 'r') as f:
        balance = pd.read_csv(f).iloc[-1]
    
    eur_bal = balance['EUR_Balance']
    btc_bal = balance['BTC_Balance']
    prev_ex_rate = balance['BTCEUR_Rate']
    try:
        current_ex_rate = df['Exchange_Rate'].iloc[-1]
    except Exception as e:
        print('Error: {}'.format(e))
        current_ex_rate = 0.0
    
    delta_pcg = ((current_ex_rate - prev_ex_rate) / current_ex_rate) * 100
    btceur_now = btc_bal * current_ex_rate

    fig_BTC={
            'data':[
                {'x':df['Last_Refreshed'], 'y':df['Exchange_Rate'], 'type':'line', 'name':'BTC'},
                {'x':df['Last_Refreshed'], 'y':df['EMA_Short'], 'type':'line', 'name':'EMA short'},
                {'x':df['Last_Refreshed'], 'y':df['EMA_Long'], 'type':'line', 'name':'EMA long'}
            ],
        }

    fig_MACD={
            'data':[
                    {'x':df['Last_Refreshed'], 'y':df['MACD'], 'type':'bar', 'name':'MACD'},
                    {'x':df['Last_Refreshed'], 'y':df['MACD_Signal'], 'type':'line', 'name':'MACD signal'}
                ]
            }
    
    table_header = [html.Thead(
        html.Tr([html.Th('Last Transaction Datetime'), html.Th('Last Transaction'), html.Th('Last Transaction Rate'), html.Th('Current Rate'), html.Th('Diff'), html.Th('EUR Wallet'), html.Th('BTC Wallet')])
        )]
    row1 = html.Tr(
        [html.Td(balance['Last_Refreshed']),
        html.Td(balance['Transaction']),
        html.Td('{}'.format('%.2f'%prev_ex_rate)),
        html.Td('{}'.format('%.2f'%current_ex_rate)),
        html.Td('{}%'.format('%.2f'%delta_pcg)),
        html.Td('{}'.format('%.2f'%eur_bal)),
        html.Td('{}/{}'.format('%.6f'%btc_bal, '%.2f'%btceur_now))
        ])
    table_body = [html.Tbody([row1])]
    table=dbc.Table(
        table_header + table_body,
        bordered=True,
        responsive=True
    )

    return fig_BTC, fig_MACD, table




if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server(host='0.0.0.0', port=8050, debug=True)
