#!/usr/bin/python3

import requests
import json
import pandas as pd
import os.path
from os import path
import datetime

import secrets
import functions

datafile = "data/btc_trend.csv" # make sure that data folder exists
walletfile = "data/bal.csv"		# make sure that data folder  exists
logfile = "log/tradingbot.log"	# make sure that log folder exists
API_KEY = secrets.alphavantage_api_key

SHORT_PERIOD = 12
LONG_PERIOD = 26
MACD_PERIOD = 9

BUY_PCG = 1
MAX_BUY = 200.0 # invest max 200 EUR and save the rest
SELL_PCG = 1
#TRANS_FEE = 0.02 # for hype is 2% (0.02)
TRANS_FEE = {'buy': 0.02, 'sell': 0.04} # for hype is buy at 2% (0.02) and sell at 4% (0.04) due to miners fees
MIN_PROFIT = 5.0 # EUR (default 0.01 EUR)

class TradingBOT():
	"""
	Class to make an API call to Alphavantage to get the currency exchange rate for two
	currencies (default is BTC to EUR)
	"""
	def __init__(self, api_key, datafile, logfile=logfile, from_currency='BTC', to_currency='EUR', debug=False, log_to_file=True):
		self.API_KEY = api_key
		
		self.datafile = datafile
		self.logfile = logfile
		self.from_currency = from_currency
		self.to_currency = to_currency

		self.DEBUG = debug
		self.LOG = log_to_file
	
		self.start()
	
	def start(self):
		# initialize error msg
		error = None

		# make an API call to get the updated market price
		try:
			market_price = json.loads(self.get_market_price(self.from_currency, self.to_currency))
		except Exception as e:
			error = e
		
		# if API call succeeds
		if error is None:
			# parse the data and write it to a csv file
			values = self.parse_data(market_price['Realtime Currency Exchange Rate'])
			new_row = pd.DataFrame(values, index=[0])

			# do some calculation and update the df
			if path.exists(self.datafile):
				df = pd.read_csv(self.datafile)
				ex_rate_s = df['Exchange_Rate']
				ema_short = functions.calc_EMA(ex_rate_s, SHORT_PERIOD)
				ema_long = functions.calc_EMA(ex_rate_s, LONG_PERIOD)
				macd = ema_short - ema_long
				macd_signal = functions.calc_EMA(macd, MACD_PERIOD)
			else:
				ema_short = new_row['Exchange_Rate']
				ema_short = new_row['Exchange_Rate']
				macd = ema_short - ema_long
				macd_signal = functions.calc_EMA(macd, MACD_PERIOD)

			new_row['EMA_Short'] = ema_short.iloc[-1]
			new_row['EMA_Long'] = ema_long.iloc[-1]
			new_row['MACD'] = macd.iloc[-1]
			new_row['MACD_Signal'] = macd_signal.iloc[-1]
			
			# write the df to a csv file
			# if the file already exists append w/o header
			if path.exists(self.datafile):
				new_row.to_csv(self.datafile, mode='a', header=False, index=False)
			else:
				new_row.to_csv(self.datafile, index=False)
			if self.DEBUG is True:
				print('{} New record written to file'.format(datetime.datetime.utcnow()))
			
			# proceed with the analysis
			self.data_analysis()

		# if the API call fails
		else:
			if self.LOG is True:
				self.log('API call error: {}'.format(error))
	
	def get_market_price(self, from_currency, to_currency):
		url = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={}&to_currency={}&apikey={}'.format(from_currency, to_currency, self.API_KEY)
		
		if self.DEBUG is True:
			print('url market price: {}'.format(url))
		
		response = requests.get(url).json()
		
		json_response = json.dumps(response, indent=4)
		
		return json_response
	
	def parse_data(self, data):
		header = []
		for item in data.keys():
			header.append(item.split('. ')[1].replace(' ', '_'))
		if self.DEBUG is True:
			print(header)
		val = []
		for item in data.values():
			val.append(item)
		if self.DEBUG is True:
			print(val)
		new_dict = dict(zip(header, val))
		if self.DEBUG is True:
			print(new_dict)

		return new_dict

	def data_analysis(self):
		df = pd.read_csv(self.datafile)
		ex_rate_s = df['Exchange_Rate']
		macd = df['MACD']
		macd_signal = df['MACD_Signal']

		trend_now = functions.find_trend_MACD(macd_signal, macd, 'current')
		trend_prev = functions.find_trend_MACD(macd_signal, macd, 'previous')

		# start trading
		functions.trade(walletfile, trend_now, trend_prev, ex_rate_s.iloc[-1], SELL_PCG, BUY_PCG, MAX_BUY, TRANS_FEE, MIN_PROFIT)

	def log(self, message):
			now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
			log = '{} {}\n'.format(now, message)

			try:
				if path.exists(self.logfile):
					with open(self.logfile, 'a') as f:
						f.write(log)
				else:
					with open(self.logfile, 'w+') as f:
						f.write(log)
			except Exception as e:
				print('Error: {}'.format(e))

if __name__ == '__main__':
	TradingBOT(API_KEY, datafile)
