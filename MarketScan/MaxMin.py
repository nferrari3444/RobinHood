# -*- coding: utf-8 -*-
"""
Created on Sun Oct  6 15:43:30 2019

@author: Nicolas
"""

import robin_stocks
import pandas as pd 
from robin_hood_Positions import PortfolioData
import datetime
from datetime import timedelta
from pandas.tseries.offsets import BDay
import time
from colorama import Fore
from colorama import Style
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
from scipy.signal import savgol_filter
from Utils_ import SymbolDerivative, symbols
from credentials import user, passWord

#r = robin_stocks
#r.login(user,passWord)


W  = '\033[0m'  # white (normal)
R  = '\033[31m' # red
G  = '\033[32m' # green
O  = '\033[33m' # orange
B  = '\033[34m' # blue
P  = '\033[35m' # purple
BOLD = '\033[1m'
BLACK = "\033[0;30m"
BROWN = "\033[0;33m"
 
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name("C:/Users/Nicolas/RobinHoodBOT/RobinHoodData-f2389423a51c.json",scope)
gc = gspread.authorize(credentials)

#Worksheet
wks = gc.open('RHData').sheet1

class Strategy():
    
    def __init__(self):
        
        self.date = datetime.datetime.now()  
        
        self.index = 2
        
    def get_data(self,symbol,timeSpan):
        '''
        Parameters:
            symbol : string with the ticker symbol of a certain stock
        timeSpan: string with the timeframe of the historical data. The alternatives
        are: day(5 minutes timeframe), week(10 minutes timeframe), year(daily timeframe)
    
        '''
    
        prices =  r.get_historicals(symbol,span=timeSpan,bounds='regular')
        bars = []
    
        for item in prices:
            date = datetime.datetime.strptime(item['begins_at'],"%Y-%m-%dT%H:%M:%SZ")
            close = float(item['close_price'])
            high = float(item['high_price'])
            low = float(item['low_price'])
            open_ = float(item['open_price'])
            volume = float(item['volume'])
    
            one_item = {'Date':date,'Open':open_,'High':high,'Low':low,'Close':close,'Volume':volume}
            bars.append(one_item)
    
        bars_df = pd.DataFrame(bars)
        # Reverse order of the dataframe showing recent dates at top
        bars_df.sort_values('Date',inplace=True,ascending=False)
        
        return bars_df
    

    def high_low(self,prices,index,symbol,HLperiods,window_SMA10,window_SMA50,window_SMA100):
        '''
        This function takes historical information of the last highs and lows prices of a symbol
        and build a matrix with the highs and lows arrays. Afterwards, it send the stock symbol 
        that meet the Inside/Double Inside Day Bars or is near 52 weeks high or 52 weeks low
        to a google sheet(RHData).
        
        Paramters:
            prices dataframe with OHLCV data for each stock
            symbol: str ticker symbol of the stock
            HLperiods: int of how many previous periods should calcualte highs
            and lows
            window: int to calculate the moving average indicator
        Returns:
            highest point  3 days before, 2 day before, 1 day before 
            lowest point  3 days before, 2 day before, 1 day before 
        '''
    
        # Get an array of unique days of the dataset
        days = prices['Date'].dt.day.unique()
    
        # Get complete unique dates for debugging 
        dates = prices['Date'].dt.date.unique()
        # Calculate the high of the bar 3 days before
    
        highs = prices['High'].iloc[:HLperiods].values
        lows = prices['Low'].iloc[:HLperiods].values
    
        # The next line, stack the highs and lows arrays in a matrix of 2 x periods dimension
        highLowMatrix = np.column_stack((highs,lows))
    
        # Calculate highs and lows for the last 3 days on the highLowMatrix
    
        threeDayHigh = highLowMatrix[2,0]
        threeDayLow =  highLowMatrix[2,1]
    
        twoDayHigh = highLowMatrix[1,0]
        twoDayLow = highLowMatrix[1,1]
    
        oneDayHigh = highLowMatrix[0,0]
        oneDayLow = highLowMatrix[0,1]
    
        
        
        fundamentals = r.get_fundamentals(symbol)
        lastPrice = float(data['Close'].iloc[0])
                  
        # Compute the moving Average Indicator with pandas on daily data
        # First reverse the prices dataframe by date, to have oldest dates at first
        # so we can keep coherence on the calculations.
    
        prices.sort_values(by='Date',inplace=True)
        closes = prices['Close']
        
        SMA_10 = round(closes.rolling(window=window_SMA10).mean().iloc[-1],3)
        SMA_50 = round(closes.rolling(window=window_SMA50).mean().iloc[-1],3)
        SMA_100 = round(closes.rolling(window=window_SMA100).mean().iloc[-1],3)
        
        trend = ''
        if (SMA_10 > SMA_50) and (SMA_50 > SMA_100):
            trend = 'UPTREND'
        
        elif (SMA_10 < SMA_50) and (SMA_50 < SMA_100):
            trend = 'DOWNTREND'
        
        else:
            trend ='UNDEFINED'
            
        date = str(datetime.datetime.now().date())
         
        for item in fundamentals:
            
            high_52_weeks = round(float(item['high_52_weeks']),3)
            
            distance52_WeeksHigh = round(((float(item['high_52_weeks']) -  lastPrice) / lastPrice) * 100,3)
            
            low_52_weeks = round(float(item['low_52_weeks']),3)
            
            distance52_WeeksLow = round(((abs(float(item['low_52_weeks']) - lastPrice )) / lastPrice) * 100,3) 

            volume = round(float(item['volume']),3)
            marketCap = round(float(item['market_cap']),3)
            
            # wks.update_cell(index,1,symbol)
          
           
            if distance52_WeeksHigh <= 10 and (trend == 'UPTREND')  and lastPrice > 30:
                
                self.index +=1
                print('Stock {} near 52 week high'.format(symbol))    
                wks.update_cell(self.index,14,high_52_weeks)
                wks.update_cell(self.index,16,distance52_WeeksHigh)
                wks.update_cell(self.index,1,symbol)
                wks.update_cell(self.index,13,lastPrice)
                wks.update_cell(self.index,20,volume)
                wks.update_cell(self.index,21,marketCap)
                
                wks.update_cell(self.index,8,SMA_10)
                wks.update_cell(self.index,9,SMA_50)
                wks.update_cell(self.index,10,SMA_100)
            
                wks.update_cell(self.index,11,date)
                wks.update_cell(self.index,12,trend)
            
                if item['pb_ratio'] != None:
                    pb_ratio = float(item['pb_ratio'])
                    wks.update_cell(self.index,18,pb_ratio)
            
                if item['pe_ratio'] != None:
                    pe_ratio = float(item['pe_ratio'])
                    wks.update_cell(self.index,19,pe_ratio)
            
            elif distance52_WeeksLow <= 10 and trend == 'DOWNTREND' and lastPrice > 30:
                
                self.index +=1
                print('Stock {} near 52 week low'.format(symbol))    
                wks.update_cell(self.index,1,symbol)
                wks.update_cell(self.index,15,low_52_weeks)
                wks.update_cell(self.index,17,distance52_WeeksLow)
                wks.update_cell(self.index,13,lastPrice)
                wks.update_cell(self.index,20,volume)
                wks.update_cell(self.index,21,marketCap)
                
                if item['pb_ratio'] != None:
                    pb_ratio = float(item['pb_ratio'])
                    wks.update_cell(self.index,18,pb_ratio)
            
                if item['pe_ratio'] != None:
                    pe_ratio = float(item['pe_ratio'])
                    wks.update_cell(self.index,19,pe_ratio)
            

                wks.update_cell(self.index,8,SMA_10)
                wks.update_cell(self.index,9,SMA_50)
                wks.update_cell(self.index,10,SMA_100)
            
                wks.update_cell(self.index,11,date)
                wks.update_cell(self.index,12,trend)
        
        # Compute the Savitzky-Golay filter on daily data
        smoothed_2dg = savgol_filter(closes, window_length = 11, polyorder = 1)
        
        print('{}Symbol{} {}'.format(BROWN,B,symbol))
        
        if (threeDayHigh > twoDayHigh) and (twoDayHigh > oneDayHigh) and (threeDayLow < twoDayLow) and (twoDayLow < oneDayLow) and lastPrice > 30:
            print('{}Symbol {} has double Inside Day Bars'.format(BOLD,symbol))

            print('Date {} High {} Low {}'.format(str(dates[2]), threeDayHigh, threeDayLow ))
            print('Date {} High {} Low {}'.format(str(dates[1]), twoDayHigh, twoDayLow ))
            print('Date {} High {} Low {}'.format(str(dates[0]), oneDayHigh, oneDayLow ))
            print('----------------------------------------------------------------------')
            
            self.index +=1
            wks.update_cell(self.index,1,symbol)
            wks.update_cell(self.index,8,SMA_10)
            wks.update_cell(self.index,9,SMA_50)
            wks.update_cell(self.index,10,SMA_100)
            
            wks.update_cell(self.index,11,date)
            wks.update_cell(self.index,12,trend)
                
            wks.update_cell(self.index,2,threeDayHigh)
            wks.update_cell(self.index,3,twoDayHigh)
            wks.update_cell(self.index,5,threeDayLow)
            
           
            wks.update_cell(self.index,6,twoDayLow)
            wks.update_cell(self.index,4,oneDayHigh)
            wks.update_cell(self.index,7,oneDayLow)
            
        elif (twoDayHigh > oneDayHigh) and (twoDayLow < oneDayLow) and lastPrice > 30:
 
            self.index +=1
            wks.update_cell(self.index,1,symbol)
            wks.update_cell(self.index,8,SMA_10)
            wks.update_cell(self.index,9,SMA_50)
            wks.update_cell(self.index,10,SMA_100)
            
            wks.update_cell(self.index,11,date)
            wks.update_cell(self.index,12,trend)
                
            twoDayRange = round(twoDayHigh - twoDayLow,2)
            oneDayRange = round(oneDayHigh - oneDayLow,2)
        
            twoDays = str((datetime.datetime.now() - BDay(2)).date())
            oneDay  = str((datetime.datetime.now() - BDay(1)).date())
            
            #self.index +=1
            
            #wks.update_cell(index,1,symbol)
            wks.update_cell(self.index,3,twoDayHigh)
            wks.update_cell(self.index,6,twoDayLow)
            wks.update_cell(self.index,4,oneDayHigh)
            wks.update_cell(self.index,7,oneDayLow)
            
         
            
            
            print('------------------------------------------------------------------')
            print('{}Symbol {} has Inside Day Bars'.format(B,symbol))
            print('Date {} High {} Low {}'.format(str(dates[1]), twoDayHigh, twoDayLow ))
            print('Date {} High {} Low {}\n'.format(str(dates[0]), oneDayHigh, oneDayLow ))
    
            print('{}{}Two days range {} One day range {}'.format(B,R,twoDayRange,oneDayRange))
            print('------------------------------------------------------------------')
    

if __name__ == '__main__':
    
    ########################################
    # Daily setup 
    init = Strategy()
    # symbols is a list that contains all ticker symbols. It is imorted from Utils
    
    position = 0
    for symbol in symbols:
        try:
            data = init.get_data(symbol,'year')
            init.high_low(data,position,symbol,5,10,50,100)
            time.sleep(3)
        except Exception as e:
            print(e)   
            print('Cannot get data for {}'.format(symbol))

    
    ###########################################
  
    
    
# https://stackoverflow.com/questions/24633618/what-does-numpy-gradient-do
    
###### Create column headers in the trade Tab

    
# Code to create the column headers in the google sheet Positiions
#columns = ['Symbol','ThreeDayHigh','TwoDayHigh','YesterdayHigh','ThreeDayLow',
 #          'TwoDayLow','YesterdayLow','SMA10','SMA50','SMA100','Date','Trend']

#dir(holdings)

#cell_list = wks.range('A2:L2')
#cell_list

#for i in range(0,len(cell_list)):
#   cell_list[i].value = columns[i]
    
#cell_list
#wks.update_cells(cell_list)

#orders = wks.worksheet('Trades')
#symbols =['NFLX','AAPL','FB','GOOG']

    