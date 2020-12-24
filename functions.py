#! /usr/bin/python3

import datetime
import pandas as pd
from os import path
import requests

def calc_EMA(series, span):
    """
    TAKE:   series with value to calculate the EMA of; averaging period
    DO:     calculate EMA with the emw function
    RETURN: return a series with the calculated EMAs
    """
    EMA = series.ewm(span=span, adjust=False).mean()
    return EMA

def find_trend_MACD(signal, MACD, step='current'):
    """
    TAKE:   df signal: EMA of the MACD; df MACD; step can be 'current' or 'previous'
    DO:     find if it's uptrend or downtrend: when signal < MACD --> uptrend, and viceversa
    RETURN: trend can be 'rising' or 'falling' - 'error' if cannot be calculated
    """
    if step == 'current':
        step = -1
    elif step == 'previous':
        step = -2
    else:
        trend = 'error'
        return trend
    
    if signal.iloc[step] < MACD.iloc[step]:
        trend = 'rising'
    else:
        trend = 'falling'
    
    return trend

def get_balance(bal_file):
    """
    TAKE:   path to file where balance is stored
    DO:     read the latest balance (last row of csv file)
    RETURN: return a dictionary with the current balance
    """
    if path.exists(bal_file):
        with open(bal_file, 'r') as f:
            df = pd.read_csv(f)
    else:
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        headers = ['Last_Refreshed', 'Transaction', 'EUR_Balance', 'BTC_Balance', 'BTCEUR_Balance', 'BTCEUR_Rate', 'Profit']
        values = [timestamp, 'SELL', 100.0, 0.0, 0.0, 0.0, 0.0]
        data = dict(zip(headers, values))
        df = pd.DataFrame(data, index=[0])
        df.to_csv(bal_file, index=False)

    balance = df.iloc[-1]
    
    return balance

def telebot_send(message):

   bot_token = '1422861121:AAHIFrQ8KFTrRXOVnPU6auxibSlqtXRUA3s'
   bot_chatID = '-422568682'
   send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + message

   response = requests.get(send_text)

   return response.json()

def update_balance(bal_file, eur_spent, btc_sold, ex_rate, transaction, profit):
    """
    TAKE:   path to file where balance is stored; EUR spent in a BUY transaction;
            BTC sold in a SELL transaction; BTC to EUR exchange rate; transaction BUY or SELL;
            expected profit in EUR
    DO:     calculate updated fields
    RETURN: none
    
    This function is called after each transaction.
    Balance information are in the form:

    | Last_Refreshed | Transaction | EUR_Balance | BTC_Balance | BTCEUR_Balance | BTCEUR_Rate | Profit |
    --------------------------------------------------------------------------------------------------
        timestamp    | BUY / SELL  | money left  | BTC left    | BTC worth      | exch rate   | EUR 

    """
    
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    last_bal = get_balance(bal_file)
    
    if transaction == 'SELL':
        eur_bal = last_bal['EUR_Balance'] + btc_sold * ex_rate
        btc_bal = last_bal['BTC_Balance'] - btc_sold
        btceur_bal = btc_bal * ex_rate
    elif transaction == 'BUY':
        eur_bal = last_bal['EUR_Balance'] - eur_spent
        btc_bal = last_bal['BTC_Balance'] + eur_spent / ex_rate
        btceur_bal = btc_bal * ex_rate

    # prepare the dictionary
    headers = ['Last_Refreshed', 'Transaction', 'EUR_Balance', 'BTC_Balance', 'BTCEUR_Balance', 'BTCEUR_Rate', 'Profit']
    values = [timestamp, transaction, eur_bal, btc_bal, btceur_bal, ex_rate, profit]

    data = dict(zip(headers, values))
    df = pd.DataFrame(data, index=[0])


    # TO-DO: make a new file at the end of each day buy renaming the existing
    #       file with the prefix 'YYYY-MM-DD_'

    # create the file if does not exist:
    if path.exists(bal_file):
        df.to_csv(bal_file, mode='a', header=False, index=False)
    else:
        df.to_csv(bal_file, index=False)


def trade(bal_file, trend_now, trend_prev, ex_rate_now, pcg_sell, pcg_buy, max_buy, fee, min_profit=0.01):
    """
    TAKE:   filepath to balance file; current and previous trends; current exchange rate;
            pcg of available btc to sell; pcg of available money to invest; max investment;
            transaction fees; minimum profit we are looking for
    DO:     check if there is a crossover and if there is, check if a legitimate transaction (i.e. if
            it is different from the last transaction), and if it is profitable or not;
            if everything is good then proceed with the transaction, update the balance file and send
            a notification via telegram
    RETURN: none
    """
    # check if there is a crossover
    if trend_now != trend_prev:
        if trend_now == 'rising':
            crossover = 'BUY' # 'bullish' # buy
        elif trend_now == 'falling':
            crossover = 'SELL' # 'bearish' # sell
    else:
        crossover = None

    if crossover is not None:
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        last_bal = get_balance(bal_file)
        ex_rate_prev = last_bal['BTCEUR_Rate']
        delta = ex_rate_now - ex_rate_prev # buy low (delta < 0) sell high (delta > 0)

        # if crossover == 'bearish' and last_bal['Transaction'] == 'BUY' and delta > 0:
        if crossover == 'SELL' and last_bal['Transaction'] == 'BUY' and delta > 0:
            btc_sold = pcg_sell * last_bal['BTC_Balance']
            profit = (abs(delta) * btc_sold) * (1 - fee)
            if profit >= min_profit:
                transaction = 'SELL'
                eur_spent = 0.0
                # TO-DO: API call to make the transaction automatically
            else:
                # if there is no profit we exit without trading
                log = '{} {} crossover. Expected profit is too little to proceed: {} EUR.'.format(timestamp, crossover, '%.2f'%profit)
                print(log)
                return
        
        # elif crossover == 'bullish' and last_bal['Transaction'] == 'SELL' and delta < 0:
        elif crossover == 'BUY' and last_bal['Transaction'] == 'SELL' and delta < 0:
            # if you have enough money, keep investing the maximum amount
            # if not, decide how much to invest
            if last_bal['EUR_Balance'] >= max_buy:
                eur_spent = max_buy
            else:
                eur_spent = pcg_buy * last_bal['EUR_Balance']
            profit = (abs(delta) / eur_spent) * (1 - fee)
            
            if profit >= min_profit:
                transaction = 'BUY'
                btc_sold = 0.0
                # TO-DO: API call to make the transaction automatically
            else:
                # if there is no profit we exit without trading
                log = '{} {} crossover. Expected profit is too little to proceed: {} EUR.'.format(timestamp, crossover, '%.2f'%profit)
                print(log)
                return
        else:
            # This is case in which there is a crossover but is the same as the last transaction.
            # In this case we exit without trading.
            log = '{} {} crossover. Not trading.'.format(timestamp, crossover)
            print(log)
            return

        # finally update the balance sheet
        update_balance(bal_file, eur_spent, btc_sold, ex_rate_now, transaction, profit)

        # and we send a telegram message
        fees = fee * 100
        msg = 'Transaction: {}\nExchange rate: {} EUR/BTC\nEstimated profit: {} EUR\nFees: {}%'.format(transaction, '%.2f'%ex_rate_now, '%.2f'%profit, '%.2f'%fees)
        telebot_send(msg) 
