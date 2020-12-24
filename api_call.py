#!/usr/bin/python3

import requests
import json
import pandas as pd
import os.path
from os import path
import datetime

output_csv = "btc_data.csv"
API_KEY = 'secret_api_key'

class callAPI():
	"""
	Class to make an API call to Alphavantage to get the currency exchange rate for two
	currencies (default is BTC to EUR)
	"""
	def __init__(self, api_key, outfile, from_currency='BTC', to_currency='EUR', debug=False, log_to_file=True):
		self.API_KEY = api_key
		
		self.outfile = outfile
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

		if error is None:
			# parse the data and write it to a csv file
			values = self.parse_data(market_price['Realtime Currency Exchange Rate'])
			df = pd.DataFrame(values, index=[0])
			
			if path.exists(self.outfile):
				df.to_csv(self.outfile, mode='a', header=False, index=False)
			else:
				df.to_csv(self.outfile, index=False)

			# print('{} New record written to file'.format(datetime.datetime.utcnow()))

		else:
			print('{} Error: {}'.format(datetime.datetime.utcnow(), e))

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


if __name__ == '__main__':
	callAPI(API_KEY, output_csv)
