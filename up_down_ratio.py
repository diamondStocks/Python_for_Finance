import os
import yfinance as yf
import datetime as dt
import pandas as pd
from pandas_datareader import data as pdr
import numpy as np
from scipy import stats

yf.pdr_override()
start =dt.datetime(2019,12,1)
now = dt.datetime.now()  

stock = input("Enter the stock symbol : ")

df = pdr.get_data_yahoo(stock,start,now)
df.reset_index(inplace=True,drop=False)
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)
df = df.tail(100)
#Find and score the Up Down Ratio of the last 50 trading days		
df['up_down'] = df['Adj Close'] > df['Open']

up = 0
down = 0
for x in range(1,50):
	if df['up_down'][-x]:
		up+=df['Volume'][-x]

	else:
		down+=df['Volume'][-x]
up_down_ratio = round(up/down,3)
if up_down_ratio > 1.0:
	print("The Up/Down Ratio is " + str(up_down_ratio) + " which is higher than 1.0 indicating strength")
else:
	print("The Up/Down Ratio is " + str(up_down_ratio) + " which is less than 1.0 indicating some weakness")