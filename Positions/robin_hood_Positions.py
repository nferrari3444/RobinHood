# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 23:51:18 2019

@author: Nicolas
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import robin_stocks
import pandas as pd 
import time
import datetime


r = robin_stocks
r.login("jancsikeresztes@gmail.com","BotTrading2019")

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)


scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('RobinHoodData-f2389423a51c.json',scope)
gc = gspread.authorize(credentials)

#Worksheet
wks = gc.open('RHData')

# holdings is the object which get the tab Positions form the RHData google sheet
holdings = wks.worksheet('Positions')

# optionHoldings get the Options tab from the RHData google sheet
optionHoldings = wks.worksheet('Options')
# Code to create the column headers in the google sheet Positiions
columns = ['Symbol','Amount','BuyPrice','BuyDate','AskSize','BidSize','LastTradePrice',
'InitialPosition','CurrentPosition','ProfitLoss','TotalProfitLoss']


class PortfolioData():
    
    def get_positions(self):
        '''
        This function get all the positions from the portfolio and
        extract relevant information of each position. 
        
        For each symbol in the portfolio, the function returns a row in 
        the Positions worksheet with information such as Symbol, Buy Price, 
        Quantity, Ask and Bid size, Last Trade Price, Initial Holding and 
        Current Holding and Profit Loss.

        '''
        positions = r.get_current_positions()

        CurrentDate = str(datetime.datetime.now().date())
        
        totalProfitLoss = 0
        for pos in positions:
            buyPrice = pd.to_numeric(pos['average_buy_price'])
            date = pos['created_at'][:-8].replace('T',' ')
            instrument_id = pos['instrument'].split('/')[-2] 
            quantity = pd.to_numeric(pos['quantity'])
            stock_data = r.get_stock_quote_by_id(instrument_id)
            symbol = stock_data['symbol']
            price = stock_data['adjusted_previous_close']
            ask_size = stock_data['ask_size']
            bid_size = stock_data['bid_size']
            lasttradeprice = pd.to_numeric(stock_data['last_trade_price'])
            update_date = pos['updated_at']
      
            if (float(pos['average_buy_price']) == 0.0):
                percent_change = 0.0
            else:
                percent_change  = (float(buyPrice)-float(pos['average_buy_price']))*100/float(pos['average_buy_price'])
        
            initialPosition = round(buyPrice * quantity,0)
            currentPosition = round(lasttradeprice * quantity,0)
            profitLoss = round(currentPosition - initialPosition,3)
            totalProfitLoss += profitLoss
            
           
            info = [symbol,quantity,buyPrice, date, ask_size, bid_size, lasttradeprice,
                    initialPosition, currentPosition, profitLoss, totalProfitLoss,CurrentDate]
            print(info)
            index = 2
            
            holdings.insert_row(info,index)
            time.sleep(1)
    
    
    def get_symbols(self,):
        '''
        This function returns the symbols that are in the Portfolio
        
        '''
        positions = r.get_current_positions()
        
        symbols = []
        for pos in positions:
            instrument_id = pos['instrument'].split('/')[-2] 
            stock_data = r.get_stock_quote_by_id(instrument_id)
            symbol = stock_data['symbol']
            symbols.append(symbol)
        
        return symbols 

  
    def get_amounts(self,):
        '''
        Returns a dictionary with the symbol as a key and the quantity of that 
        symbol on the portfolio as value
        
        '''
        positions = r.get_current_positions()
        
        posSize = {}
        
        for pos in positions:
            instrument_id = pos['instrument'].split('/')[-2] 
            stock_data = r.get_stock_quote_by_id(instrument_id)
            symbol = stock_data['symbol']
            posSize[symbol] = pos['quantity']
            
        return posSize
                   
    
    def get_latest_data(self,symbol):
        '''
        Returns a dataframe with the latest data for the symbol with a 5 minute
        interval
        '''
        data = r.get_historicals(symbol,'day')
        
        
        return data
        
        
    def get_options_data(self):
        '''
        This function call the open options positions and extract the 
        symbol, type, price quantity and date.
        
        Returns a dataframe with the options positions
        '''
        options = r.get_open_option_positions()
        
        CurrentDate = str(datetime.datetime.now().date())
        
        for item in options:
            symbol = item['chain_symbol']
            positionType = item['type']
            buyPrice = item['average_price']
            quantity = item['quantity']
            
            dates =  item['created_at'][:-8].replace('T',' ')
            optionId = item['option'].split('/')[-2]
            
            instrumentData = r.get_option_instrument_data_by_id(optionId)
            expiry = instrumentData['expiration_date']
            optionType = instrumentData['type']
            strike = instrumentData['strike_price']
            underlying = float(r.get_latest_price(symbol)[0])
            marketData =  r.get_option_market_data_by_id(optionId)
            
            askPrice = marketData['ask_price']
            bidPrice = marketData['bid_price']
            BreakEvenPrice = marketData['break_even_price']
            
            lastTradePrice = marketData['last_trade_price']
            askSize = marketData['ask_size']
            bidSize = marketData['bid_size']
            delta = marketData['delta']
            gamma = marketData['gamma']
            theta = marketData['theta']
            vega = marketData['vega']
            
            open_interest = marketData['open_interest']
            
            impliedVolatility = marketData['implied_volatility']
            
            info = [dates,symbol,optionType,positionType,expiry,strike,underlying,buyPrice,askPrice,bidPrice,BreakEvenPrice,
                    lastTradePrice,askSize,bidSize,delta,gamma,theta,vega,open_interest,impliedVolatility,CurrentDate]
                    
            index = 3
            optionHoldings.insert_row(info,index)
            
            time.sleep(1)


if __name__ == "__main__":
    
    inst = PortfolioData()
    
    options = inst.get_options_data()
    pos = inst.get_positions()
    
    #print(options)
    #print(pos)
    
   
# Code to create the column headers in the google sheet Positiions
#columns = ['Date','Symbol','OptionType','Expiry','Strike','Underlying','BuyPrice',
#           'ask','bid','breakEvenPrice','lastPrice','askSize','bidSize',
#           'delta','gamma','theta','vega','OI','IV']


#           'TwoDayLow','YesterdayLow','SMA10','SMA50','SMA100']

#dir(holdings)
#cell_list = optionHoldings.range('A2:S2')
#cell_list
#for i  in range(0,len(cell_list)):
#   cell_list[i].value = columns[i]
    
#cell_list
#optionHoldings.update_cells(cell_list)