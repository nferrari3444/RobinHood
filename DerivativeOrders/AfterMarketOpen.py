# -*- coding: utf-8 -*-
"""
Created on Sun Oct 13 16:30:07 2019

@author: Nicolas
"""
import robin_stocks
import pandas as pd 
import datetime
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
import time   
from datetime import timedelta

r = robin_stocks
r.login("jancsikeresztes@gmail.com","BotTrading2019")

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('RobinHoodData-f2389423a51c.json',scope)
gc = gspread.authorize(credentials)

#Worksheet
wks = gc.open('RHData')

orders = wks.worksheet('Trades')

api_key = 'RQKFECZIU89JZK5T'

print(orders.get_all_records())

class Trades():
    
    def __init__(self):
        
        self.index = 5 
    
    
    def marketOpen(self,symbol,minutes):
        '''
        This function will store prices after market open to allow the script to calculate
        price derivative after market open. The output of this function will be the input for
        calculating the derivative of the price after certain minutes from market Open.
        
        Parameters:
            symbol: string with the ticker symbol
            minutes: int, minutes after market open to store prices. The highest frequency 
            in RobinHood API for getting prices is 5 minutes. This means that prices comes in
            5 minutes interval such as 9:30, 9:35, 9:40, 9:45, 9:50, etc. For this reason we 
            use the Alpha Vantage API which provide data in one minute frequency
        
        Returns:
            closePrices: list with the first values of the stock price after the amount of 
            minutes from market open.
        '''
        
        # This API returns 100 values for the last prices on minute level
        url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={}&interval=1min&apikey={}'.format(symbol,api_key)
        data = requests.get(url)

        data = data.json()
        af_data = data['Time Series (1min)']
        
        minuteData = []
        for key,value in af_data.items(): 
            date = datetime.datetime.strptime(key,"%Y-%m-%d %H:%M:%S")
            close = float(value['4. close'])
            volume = float(value['5. volume'])
            minuteData.append({'date':date,'close':close,'volume':volume})
        
        
        # Convert the marketOpenData to a DataFrame and get the values from current day
        minuteData_df = pd.DataFrame(minuteData)
        #print(minuteData_df)
        
        # If we are at weekend, we can substract days with timedelta
        currentDay = (datetime.datetime.now().day) # - timedelta(days=2)).day
        marketOpenData = minuteData_df[minuteData_df['date'].dt.day == currentDay]
        #print(marketOpenData)
        
        # Reverse the Dataframe to have earlist values at top
        marketOpenData.sort_values('date',inplace=True)
        # Get amount of minutes after market Open 
        
        print(marketOpenData.head())
        closePrices = marketOpenData['close'].iloc[:minutes]
        
        return closePrices


    def Orders(self,prices):
        '''
        This function trigger orders based on the prices after market open. At first it 
        calculates the derivative/gradients of the prices and if the slope is positive
        trigger a market order to buy.
    
        '''

        minuteValues = np.array(prices)
        print('First Minute prices of Symbol {} are {}'.format(minuteValues,symbol))
        slope = np.gradient(minuteValues) 
        print('Gradients of Symbol {} is {}'.format(symbol,slope))
        slopeSign = np.sum(np.sign(slope))
    
        if slopeSign < 0:
            print('Negative Slope for symbol {} after {} minute from market Open'.format(symbol,minutes))
            print('Derivative is {}'.format(slopeSign))
            print('------------------------------------------------------------------------')
            
        if slopeSign > 0:
            print('Positive Slope for symbol {} after {} minute from market Open'.format(symbol,minutes))
            print('Derivative is {}'.format(slopeSign))
           
            # The next line trigger a market order to buy the symbol specified with a quantity of 1.
            # I comment the line with # to test the script without triggering orders
            #buyOrder = r.order_buy_market(symbol,1)
                
            # Retrieve information from the buyOrder object
#            price = round(float(buyOrder['price']),3)
#            quantity = round(float(buyOrder['quantity']),2)
#            side = buyOrder['side']
#            stop_price = buyOrder['stop_price']
#            symbolData = r.get_instrument_by_url(buyOrder['instrument'])
#            symbol = symbolData['symbol']
#            stockName = symbolData['name']
#            dayTradeRatio = symbolData['day_trade_ratio']
#            bloomberg_id = symbolData['bloomberg_unique']
                
#            if buyOrder['executions'] != []:
#                filled = True 
#            else: 
#                filled = False
                
#            submittedTime = buyOrder['created_at'][:-8].replace('T',' ')
#            orderInfo = [symbol,stockName,price,quantity,side,filled,submittedTime,stop_price,dayTradeRatio,bloomberg_id]
#            index +=1

#            This line will insert the orderInfo object in the Google Sheet             
#             orders.insert_row(orderInfo,index= index)
               
            print('-------------------------------------------------------------------------------------')
         
                     
    

if __name__ == '__main__':
    
    symbols = ['SYY','DOCU',"ABBV" ,"MDLZ" ,"ZEN" ,"SO" ,"OKTA" ,"GIS", "WELL", "OMC"]
    
    index = 2
    minutes = 5
    for symbol in symbols:
        trades = Trades()
        prices = trades.marketOpen(symbol,minutes)
        
        trades.Orders(prices)
        time.sleep(5)  
        #    if currentTime >= marketOpen:
    #        if datetime.datetime.now() - marketOpen == minutes:
    
           
        
        