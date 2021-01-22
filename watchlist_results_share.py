#############################################################################
# Watchlist results compiler, check your watch list every weekend			
# 																			
# Written by: Diamond https://twitter.com/Diamond_Stock						
# Improvements to be made: Need to tighten up the rules on the weekly close 
#                          range to consider market downtrends. Feel free to
#						    @ me with more ideas   							
#						             
# version 1.3																
#																			
#############################################################################

import datetime as dt
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
import os
import time
import numpy as np
import calendar
from tkinter import Tk
from tkinter.filedialog import askopenfilename

##Setup pandas override for Yahoo API
yf.pdr_override()

## Get time frames, probably a better way to filter through one data table, tail will not work as it does not take into account holidays
## Couldn't get the index to work properly due to the datetimeindex being confusing for me, will improve at some point
now = dt.datetime.now()
start = now - dt.timedelta(days=now.weekday())
start2 = now - dt.timedelta(weeks = 11)


## place the path of your csv file here, this should work with excel docs as well, just ensure the colume with 
## the stock symbols is labeled 'Symbol'. Also ToS prints out watch lists with headers, you will have to delete it manually
## at some point I will have the script manually query whether its a csv or excel doc and then clean up the headers if need be
root = Tk()
ftypes = [("CSV Files","*.csv"),(".xlsm","*.xlsx",".xls")]
ttl  = "Watchlist Import"
dir1 = 'C:\\USE\\YOUR\\DIR\\HERE'
filePath = askopenfilename(filetypes = ftypes, initialdir = dir1, title = ttl)
stockList = pd.read_csv(filePath)

## Enter in your saved path
savePath = r"D:\SAVE_YOUR_DIR_HERE"

## grab today without the timecode BS
today = dt.datetime.date(now.now())

## set up the file path structure and check to seee if it exists
path = os.path.join(savePath+"\\","watch_list_results",str(today))
if not os.path.exists(path):
	os.makedirs(path)

## establish your massive string obj to dump text into. Maybe a dictionary would be more elegant, but Im not elegant
finalText = ''
simpleText = ''


weeklyResults = pd.DataFrame(columns=['Symbol','Percent Change','Week Open','Week Close','Week Low','Week High','Weeks Volume','Low Date','Low Day Name','Shake Out','Weekly Close Range'])


## Begin the for loop to iterate over each stock
for i in stockList.index:
	stock = str(stockList["Symbol"][i]).upper()
	df = pdr.DataReader(stock,data_source='yahoo',start =start,end= now)
	df.reset_index(inplace=True,drop=False)
	df.set_index('Date', inplace=True)
	
	## establish the open, close, high, low, and percent change for the week
	p_open = round(df['Open'][0],2)
	p_close = round(df['Adj Close'][-1],2)
	p_delta = round(100*(p_close - p_open)/p_open,2)
	p_high = round(df["High"].max(),2)

	## we don't round low here as I want to filter by it next and need it to match the dataframe
	p_low = df["Low"].min()

	## grab the date index and properly format it so it's readable
	p_low_day = df.index[df['Low']==p_low].format()[0]

	## .weekday() command returns an int value for each day of the week, pretty cool
	low_day_int = dt.datetime.strptime(p_low_day,'%Y-%m-%d').weekday()

	## day_name gives us the actually week day name based on the above int, I know I could merge this into one line
	## but figured it'd be better for readability. Plus one day I hope to get paid by the line
	p_low_day_name = calendar.day_name[low_day_int]

	## switch the low day from the goofy datetimeindex the data frame uses over to something we can actually use
	p_low_date = dt.datetime.strptime(p_low_day,'%Y-%m-%d')

	## whatever your max stop loss usually is. William O'Neil reccomends 7-8% for uptreads and 3% for chop and bear markets
	shakePercent = 5

	## find your max draw down for the week
	shakeOut =  round(100*(p_low - p_open)/p_open,2)

	##find weekly volume
	weekVol = df['Volume'].sum()

	##find weekly closing range
	weekCloseRange = round(((p_close-p_low)/(p_high-p_low))*100,2)


	weeklyResults = weeklyResults.append({'Symbol': stock, 'Percent Change': p_delta, 'Week Open': p_open, 'Week Close': p_close,'Week Low': p_low, 'Week High': p_high,
										  'Weeks Volume': weekVol,'Low Date':p_low_date ,'Low Day Name':p_low_day_name ,'Shake Out':shakeOut,'Weekly Close Range': weekCloseRange }, ignore_index = True)


weeklyResults.sort_values(by=['Percent Change'], inplace = True ,ascending = False, ignore_index = True)
print(weeklyResults)

for i in weeklyResults.index:

	stock=weeklyResults['Symbol'][i]
	week_open = weeklyResults['Week Open'][i]
	week_close = weeklyResults['Week Close'][i]
	week_close_range = weeklyResults['Weekly Close Range'][i]
	percentChange = weeklyResults['Percent Change'][i]
	week_low = weeklyResults['Week Low'][i]
	week_high = weeklyResults['Week High'][i]
	week_vol = weeklyResults['Weeks Volume'][i]
	low_date = weeklyResults['Low Date'][i]
	low_date_name = weeklyResults['Low Day Name'][i]
	shakeout = weeklyResults['Shake Out'][i]
	shakePercent = 5

	## here's where you can tell I dont have a CS degree.  We establish the text file contents here
	finalText+=('\n'+stock+' weekly stats: ')
	finalText+=('\n'+'Open: $'+str(week_open))
	finalText+=('\n'+'Close: $'+str(week_close))
	finalText+=('\n'+stock + ' % Changed: '+str(percentChange)+'%')
	finalText+=('\n'+'Weekly High: $' + str(week_high))
	finalText+=('\n'+'Weekly Low: $' + str(round(week_low,2)))
	## this is gross, I don't like having to query the data twice, its not efficient, but my daughter woke up from a nap, so I cheated here as I knew it would work
	df2 = pdr.DataReader(stock,data_source='yahoo',start =start2,end= now)
	weeklydata= df2['Volume'].resample('W-MON').sum()
	weeklyAvgVol = round(weeklydata.rolling(window=10).mean(),2)
	weekVol_percent = round((week_vol/weeklyAvgVol[-1])*100,2)

	## check to see if you'd have gotten shaken out. Work on those entry points...
	if(-shakePercent > shakeout):
		finalText+=('\n'+'If bought on weekly open you would have been shaken out for a 5% loss on '+ str(low_date_name) + " "+ str(low_date.month)+"-"+str(low_date.day))
	else:
		## set the 50 day sma, feel free to add whatever here
		df2["SMA_"+str(50)] = round(df2.iloc[:,4].rolling(window=50).mean(),2)

		##grabbing the last value of the 50sma table
		final_sma50 = round(df2['SMA_50'][-1],2)

		## getting the % different between the closing price on the last trading day and the last 50sma
		above50sma = round(((week_close/final_sma50)-1)*100,2)
		## more sweet non-pythonic text blocks cuz I know you love them. This checks to see if the difference is negative, meaning the price is below the 50sma 
		## this is usually a sign that it's lost a lot of strength and doesn't have the same support it would above

		if(above50sma<0):
			finalText+=('\n'+stock + " has closed below it's 50 day sma of $"+ str(final_sma50) + " and should be monitored for weakness")
		else:
			finalText+=('\n'+'If bought on weekly open no shake out has occured. ' + str(stock) + " is currently "+str(above50sma)+"% above it's 50 day sma of $" + str(final_sma50))

			
	## Check in on the weekly volume and let me know if its somewhat normal, or under accum or dist. Need to clean this up
	if(week_vol > weeklyAvgVol[-1] and week_close > week_open):
		if(weekVol_percent>120):
			finalText+=('\n'+stock+' could be under accumulation with a weekly volume incease of '+str(round(weekVol_percent-100,2))+'% more than the average')
		else:
			finalText+=('\n'+stock+' had above average volume this week and closed above its weekly open of $'+str(week_open))
	elif(week_vol < weeklyAvgVol[-1] and week_close > week_open):
		finalText+=('\n'+stock+' had below average volume this week and closed above its weekly open of $'+str(week_open))
	elif(week_vol > weeklyAvgVol[-1] and week_close < week_open):
		if(weekVol_percent>120):
			finalText+=('\n'+stock+' could be under distribution with a weekly volume decrease of '+str(round(weekVol_percent-100,2))+'% less than the average')
		else:
			finalText+=('\n'+stock+' had above average volume this week and closed below its weekly open of $'+str(week_open))
	elif(week_vol < weeklyAvgVol[-1] and week_close < week_open):
		finalText+=('\n'+stock+' had below average volume this week and closed below its weekly open of $'+str(week_open))
	if week_close_range >=50:
		finalText+=('\n'+stock+' had a weekly closing range of '+str(week_close_range)+"%"+' which can be considered bullish')
	else:
		finalText+=('\n'+stock+' had a weekly closing range of '+str(week_close_range)+"%"+' which can be considered bearish')
	finalText+=('\n'+"==========================================================================================================="+'\n')

	## adding a simple print for twitter purposes
	simpleText += '\n'+stock+': '+ str(percentChange)+'%'
## print to the terminal if you want a fast read out of it

print(finalText)



## We are grabbing the previous path variable from above, then creating the text file name based on the date so you don't write over previous files
textFile = path+"\\"+str(today)+"_watchListResults.txt"
simpletextFile = path+"\\"+str(today)+"_simpleWatchListResults.txt"
## this is a fancy way of writing to a text file that I found on stack overflow because 90% of coding is googling someone elses work.
## the w+ means its writable and if you tagged this inside the for loop it would just append to the file over and over again. The write lines
## command just prints off the big text list to the file.
with open(textFile,'w+') as out_file:
	out_file.writelines([finalText])
with open(simpletextFile,'w+') as out_file:
	out_file.writelines([simpleText])
