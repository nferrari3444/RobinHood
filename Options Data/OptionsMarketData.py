# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 18:44:26 2019

@author: Nicolas
"""

import robin_stocks
r = robin_stocks
r.login("jancsikeresztes@gmail.com","BotTrading2019")

from pandas import ExcelWriter
import pandas as pd 
import time
import datetime

# HOG
# ARNC

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)

chain = r.get_chains('SYY')

expirationDates =  chain['expiration_dates'] 

#contracts = r.find_options_for_stock_by_expiration('HOG','2019-11-22')
#contracts = r.find_options_for_stock_by_expiration('ARNC','2019-11-22')



contracts = r.find_options_for_stock_by_expiration('SYY','2019-11-22')


option = r.find_options_for_stock_by_expiration_and_strike('SYY','2019-11-22','80',optionType='call')

option_data = []

for contract in contracts:
    adjPrice = float(contract['adjusted_mark_price'])
    askPrice = contract['ask_price']
    bidPrice = contract['bid_price']
    askSize = contract['ask_size']
    bidSize = contract['bid_size']
    
    prevClose = contract['previous_close_price']
    lastTradePrice = contract['last_trade_price']
    
    delta = contract['delta']
    gamma = contract['gamma']
    theta = contract['theta']
    vega = contract['vega']
    
    IV = contract['implied_volatility']
    type_ = contract['type']
    strike = contract['strike_price']
    volume = contract['volume']
    option_data.append({'adjustedPrice':adjPrice,'askPrice':askPrice,'bidPrice':bidPrice,
                        'askSize':askSize,'bidSize':bidSize, 'previousClose':prevClose,
                        'lastTradePrice':lastTradePrice, 'delta':delta, 'gamma':gamma,
                        'theta':theta,'vega':vega, 'type':type_, 'strike':strike,
                        'volume':volume,'IV':IV})

option_df = pd.DataFrame(option_data)    
    
      
  
writer = ExcelWriter('SYY.xlsx')
option_df.to_excel(writer,'Sheet5')
writer.save()
