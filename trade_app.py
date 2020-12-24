import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
from dash.dependencies import Input, Output

import pandas as pd
import datetime
import functions
from api_call import callAPI, API_KEY

SHORT_PERIOD = 12
LONG_PERIOD = 26
MACD_PERIOD = 9

PCG_INVEST = 1
MAX_INVESTMENT = 200.0 # invest max 200 EUR and save the rest
PCG_SELL = 1
TRANSACTION_FEE = 0.02 # for hype is 2% (0.02)
MIN_PROFIT = 0.01 # EUR

WALLET_CSV = "bal.csv"
BTC_CSV = "btc_trend.csv"

# make an instance of Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

app.layout = dbc.Container([
        html.H1('BTC trend graph'),
        dcc.Graph(id='BTC_graph'),
        dcc.Graph(id='MACD_graph'),
        html.Div(id='table'),
        dcc.Interval(
            id='timer',
            interval=60*1000, # in millis,
            n_intervals=0
        )
])


@app.callback([Output('BTC_graph', 'figure'),
            Output('MACD_graph', 'figure')],
            Output('table', 'children'),
            [Input('timer', 'n_intervals')])
def update(n):
    # TO-DO: add columns EMA_short, EMA_long, MACD and MACD_EMA to the df
    #       and update it with new records
    
    # make the API call every 5 minutes
    if datetime.datetime.utcnow().minute % 5 == 0:
        callAPI(API_KEY, BTC_CSV)

    # open the dataframe
    df = pd.read_csv(BTC_CSV)
    ex_rate_s = df['Exchange_Rate']

    # analyse the trend
    ema_short = functions.calc_EMA(ex_rate_s, SHORT_PERIOD)
    ema_long = functions.calc_EMA(ex_rate_s, LONG_PERIOD)
    macd = ema_short - ema_long
    macd_signal = functions.calc_EMA(macd, MACD_PERIOD)

    # start trading
    trend_now = functions.find_trend_MACD(macd_signal, macd, 'current')
    trend_prev = functions.find_trend_MACD(macd_signal, macd, 'previous')

    # trade(df, ex_rate_s, trend_now, trend_prev)
    functions.trade(WALLET_CSV, trend_now, trend_prev, ex_rate_s.iloc[-1], PCG_SELL, PCG_INVEST, MAX_INVESTMENT, TRANSACTION_FEE, MIN_PROFIT)
    
    balance = functions.get_balance(WALLET_CSV)
    
    eur_bal = balance['EUR_Balance']
    btc_bal = balance['BTC_Balance']
    prev_ex_rate = balance['BTCEUR_Rate']
    delta_pcg = ((ex_rate_s.iloc[-1] - prev_ex_rate) / ex_rate_s.iloc[-1]) * 100
    btceur_now = btc_bal * ex_rate_s.iloc[-1]

    fig_BTC={
            'data':[
                {'x':df['Last_Refreshed'], 'y':df['Exchange_Rate'], 'type':'line', 'name':'BTC'},
                {'x':df['Last_Refreshed'], 'y':ema_short, 'type':'line', 'name':'EMA short'},
                {'x':df['Last_Refreshed'], 'y':ema_long, 'type':'line', 'name':'EMA long'}
            ],
        }

    fig_MACD={
            'data':[
                    {'x':df['Last_Refreshed'], 'y':macd, 'type':'bar', 'name':'MACD'},
                    {'x':df['Last_Refreshed'], 'y':macd_signal, 'type':'line', 'name':'MACD signal'}
                ]
            }
    
    table_header = [html.Thead(
        html.Tr([html.Th('Trend'), html.Th('Last Transaction Rate'), html.Th('Current Rate'), html.Th('Diff'), html.Th('EUR Wallet'), html.Th('BTC Wallet')])
        )]
    row1 = html.Tr(
        [html.Td(trend_now),
        html.Td('{}'.format('%.2f'%prev_ex_rate)),
        html.Td('{}'.format('%.2f'%ex_rate_s.iloc[-1])),
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
    app.run_server(debug=True)