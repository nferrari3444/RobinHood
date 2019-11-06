# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 17:09:25 2019

@author: Nicolas
"""

import robin_stocks
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import robin_stocks
import pandas as pd 
from robin_hood_Positions import PortfolioData
import datetime
from collections import defaultdict
import time 
from datetime import timedelta


r = robin_stocks
r.login("jancsikeresztes@gmail.com","BotTrading2019")


class TrailingOrders():
    
    def __init__(self,days, minutes):
        '''
        Parameters:
            
            days: negative integer which refert to the amount of days to look back
            for the highest price of the symbol. If it is zero, the function will look for 
            the high price of the current day. 
        
            Contrary if is is less than zero, the integer paramter refer to the amount of previous days to look
            for the highest price
        '''
        
        self.set_trailing_stop = {}
        
        self.days = days
        self.Time = datetime.datetime.now()
        self.minutes = minutes 
        self.updatemins = self.Time + timedelta(minutes)
        
    def maxPrices(self,):
        '''
        This function loop over all positions in the portfolio and for each symbol 
        extract historical data based on the days paramter above. Then, it gets 
        the maximum price and the date of this point
       
        Returns:
            highPrices: dictionary list that has symbol as key and highest price 
            over the desired period and the datetime in which that price was reached
            as values of the dictionary.
            Example defaultdict(list, {'ACB': [11.0, '2018-10-18 '], 'AMBA': [67.146, '2019-09-11 '],
            'AMD': [35.55, '2019-08-09 '], 'BGS': [31.6, '2018-12-14 '],
            'CDXS': [23.05, '2018-12-03 '],
        '''
       
        positions = r.get_current_positions()
        highPrices = defaultdict(list)
    
        for pos in positions:
            
            buyPrice = pd.to_numeric(pos['average_buy_price'])
            date = pos['created_at'][:-8].replace('T',' ')
            instrument_id = pos['instrument'].split('/')[-2] 
            quantity = pd.to_numeric(pos['quantity'])
            stock_data = r.get_stock_quote_by_id(instrument_id)
            symbol = stock_data['symbol']
            # print('Symbol {} price {}'.format(symbol,buyPrice)) 
    
            # Get historical data for the symbol
            if self.days <  0:
                prices =  r.get_historicals(symbol,span='year',bounds='regular')
                prices = prices[self.days:]
                
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
                bars_df.set_index('Date',inplace=True)
        
                highPrices[symbol].append(bars_df['High'].max())
                highPrices[symbol].append(str(bars_df['High'].idxmax())[:-8])
                yesterdayPrice = bars_df['Close'].iloc[0]    
    
                print('{} max Price is {} on date {} previousClose {} buyPrice {}'.format(symbol,highPrices[symbol][0],highPrices[symbol][1],yesterdayPrice,buyPrice))
        
                time.sleep(1)
            
            # Get highest price for current day for the symbol
            elif self.days == 0:
                prices =  r.get_historicals(symbol,span='day',bounds='regular')
                
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
                bars_df.set_index('Date',inplace=True)
        
        
                bars_df = bars_df[bars_df.index >= datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month,datetime.datetime.now().day,13,30)]
                
                
                highPrices[symbol].append(bars_df['High'].max())
                highPrices[symbol].append(str(bars_df['High'].idxmax()))
                
                print('{} max Day Price is {} on Time {} buyPrice {}'.format(symbol,highPrices[symbol][0],highPrices[symbol][1],buyPrice))
        
                time.sleep(1)
    
                # Get the highest price for the stock in a timespan of 1 year

        return highPrices 
    

    def trailingStop(self,maxPrices):
        '''
        This function compare the latest price of each symbol in the portfolio with it highest
        value in the highPrices dictionary. Every moment will set a trailing stop for
        take profit since the order is placed and the stock is in the portfolio
    
        Parameters:
            maxPrices dictionary. This dictionary is generated in the previous 
            function
            
        Returns:
            set_trailing_stop: dictionary with symbol key and highest price within one year as 
            value. All symbols that have broken it highest price will be in this dictionary
        '''
    
        symbols = PortfolioData.get_symbols(self,)
        SymbolSize = PortfolioData.get_amounts(self,)
        # Get the lastprice of the stock
        # maxPrices =  self.maxPrices()
        
        trailingStop = {}
        
        for symbol in symbols:
         
            latestPrice = r.get_latest_price(symbol)
            highestPrice =  maxPrices[symbol][0]
            if float(latestPrice[0]) >= highestPrice and float(SymbolSize[symbol]) >0 and symbol not in trailingStop.keys():
                
                self.set_trailing_stop[symbol] = highestPrice
                print('------------------------------------------------------------------------')
                print('Symbol {} latest price {} is higher than max price {}'.format(symbol,latestPrice,highestPrice))
                
            else:
                print('{} Current Price {} is lower than maxPrice of {}'.format(symbol,latestPrice,highestPrice))
                time.sleep(1)
        
        return self.set_trailing_stop
       
        
    
    def set_trailing_order(self,trailing,trailStop):
        '''
        The function loop over all the symbols whose prices break it
        maxPrice and compare the last Price in every moment with the highPrice.
        If the last price is greater than the highPrice, and the current price is
        higher than the previous price (up movement), the trailPrice is updated, 
        else the trailPrice is the same than it previous level
        
        
        Parameter:
            trailing: dictionary with the symbols that should look for trailing orders
            trailStop: float to determine the distance between the latest price 
            and the orderTrail price       
        '''
        
    
        prices = defaultdict(list)
        trailOrderPrice = defaultdict(list)
        sellOrder = {}
        
        for symbol, highPrice in trailing.items():
            
           
            while len(prices[symbol]) <= 5:
                latestPrice = r.get_latest_price(symbol)
                latestPrice = float(latestPrice[0])
                prices[symbol].append(latestPrice)
                
                print('---------------------------------------------------')
                print('Populating prices of symbol {} latestPrice {}'.format(symbol,latestPrice))
            
                time.sleep(10)
                if len(trailOrderPrice[symbol]) == 0:    
                    trailOrderPrice[symbol].append(prices[symbol][0] * trailStop)
                    print('First value of trailPrice {} for symbol {}'.format(round(trailOrderPrice[symbol][0],3), symbol))
 
                
          # print('Extended Time {}'.format(self.Time + timedelta(minutes=self.minutes)))
            while datetime.datetime.now() <= self.Time + timedelta(minutes= self.minutes):
                # Initialize the trailOrderPrice with X % from the current price
                    
                #if len(prices[symbol]) >= 20:
                    #    maxValue = max(prices)
            
            # the trailOrderPrice for each symbol track the path of the price by a certain
            # percent distance. When the price break the highest price and continue
            # rising
                
                latestPrice = r.get_latest_price(symbol)
                latestPrice = float(latestPrice[0])
                prices[symbol].append(latestPrice)
                
                if prices[symbol][-1] > prices[symbol][-2] and prices[symbol][-1] > max(prices[symbol][:-1])  and prices[symbol][-1] > highPrice:
                
                    print('---------------------------------------------------')
                    print('Current Price is {}'.format(prices[symbol][-1]))
                    print('Past Price is {}'.format(prices[symbol][-2]))
                    
                    # UPDATE THE TRAILORDERPRICE when the price is rising up USING
                    # THE TRAILSTOP FLOAT NUMBER AND THE LATEST PRICE
                    updatePrice = prices[symbol][-1] * trailStop
                    trailOrderPrice[symbol].append(updatePrice)
                    print('Increase trailing stop for symbol {} to {}'.format(symbol,updatePrice))
        
                # If the price does not rise, the trailPrice is equal to it previous level
                else:
                    
                    print('Current Price is {}'.format(prices[symbol][-1]))
                    print('Past Price is {}'.format(prices[symbol][-2]))
                    
                    trailOrderPrice[symbol].append(trailOrderPrice[symbol][-1])
                    print('Trail stop keep on the same level {} on time {}'.format(round(trailOrderPrice[symbol][-1],4),str(datetime.datetime.now())))
            
                    
                #print('Time now {}'.format(datetime.datetime.now()))
                #print('Extended Time {}'.format(self.Time + timedelta(minutes=self.minutes)))
                time.sleep(10)
                    
                ## HAVE COMMENTED THESE LINES BECAUSE THIS IS THE CONDITION TO 
                # LIQUIDATE THE POSITION SENDING A MARKE ORDER TO SELL
                
                #if latestPrice <= trailOrderPrice[symbol]:
                #    sellOrder[symbol] = r.order_sell_market(symbol)
            
       #     r.order_sell_market(symbo)
       # trailingStop[symbol] = latestPrice * 0.95
                
       #         takr.order_sell_market(symbol)
                
if __name__ == '__main__':
    
    # Here you insert the integer number to track highest price over a certain 
    # period. If the number is zero, the function will look for the highest price
    # at current day. If it is -20, will look for the highest price over a period
    # of 20 previous days.
    
    days = 0
    currentTime = datetime.datetime.now()
    
    
    run = TrailingOrders(days,10)
    
    highPrices = run.maxPrices()    
    symbolsToTrail = run.trailingStop(highPrices)
    
    run.set_trailing_order(symbolsToTrail,0.9)
    
    
    
    
    
    