# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 18:44:26 2019

@author: Nicolas
"""
import robin_stocks

r = robin_stocks
r.login("jancsikeresztes@gmail.com","BotTrading2019")

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import gspread_dataframe as gd
from pandas import ExcelWriter
import pandas as pd 
import time
import datetime
from datetime import timedelta


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)

# The steps below are for authenticate through the Google Sheet API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('RobinHoodData-f2389423a51c.json',scope)
gc = gspread.authorize(credentials)

#Worksheet
wks = gc.open('RHData')

# optionScreener is the object to send data to the OptionsScreener tab in the Google Sheet
optionScreener = wks.worksheet('OptionsScreener')

# PCR is the object to send data to the PutCallRatio/IV tab
PCR = wks.worksheet('PutCallRatio/IV')



def expirationDates(symbols):
    '''
    This function get the expiration dates for each symbol. Will retrieve expiration dates
    for one month ahead. Then we will use these expiration dates to obtain the chain for 
    each expiration date
    
    returns:
        dates: list with expiration dates for all valid symbols
        symbols: validated symbol list, as there are some symbols in which the API 
        doesn't have data, and this function would remove these symbols. 
        validSymbols : list of dictionaries that contains symbols as keys and expi-
        ration dates for each symbols as values. Example:
       [{'SPY': '2019-11-06'}, {'SPY': '2019-11-25'},
        {'SPY': '2019-11-08'},   {'SPY': '2019-11-27'},...
 
    '''
    
    symbolsDates = []
    for symbol in symbols:
        
        try:
            chain = r.get_chains(symbol)

            expirationDates =  chain['expiration_dates'] 
            
            for date in expirationDates:
                if datetime.datetime.now().date() + timedelta(days=31) >= datetime.datetime.strptime(date,'%Y-%m-%d').date():
                    symbolsDates.append({str(symbol):date})
                    
            
            print('Dates for {}'.format(symbol))
        except Exception as e:
        
            print(e)   
            print('For contract {} cannot get chain data'.format(symbol))  
            
    symbols = []
    dates = []
    
    # Extract key(symbols) and values(dates) from the symbolsDates dictionary and 
    # append them to the symbols and dates lists respectively
    for item in symbolsDates:
        for k, v in item.items():
            if k not in symbols:
                symbols.append(k)
            if v not in dates:
                dates.append(v)
    
    return dates, symbols, symbolsDates


def option_contract(symbol, expiration,strike,optionType):
    '''
    Parameters:
        symbol: str with the ticker symbol of the stock
        expiration: str with the expiration date of the contract
        strike: str with the strike price of the option contract
        optionType: 'call' or 'put'
    Returns:
        price: current Price of the contract
        IV: Implied Volatility of the contract
    '''
    
    option = r.find_options_for_stock_by_expiration_and_strike(symbol,expiration,strike,optionType)

    price = float(option[0]['adjusted_mark_price'])
    
    if option[0]['implied_volatility'] != None:
        IV = float(option[0]['implied_volatility'])
    
    else:
        IV = ''
        
    return price,IV
    
option_contract('SYY','2019-11-29','80','call')

def contracts_by_expiration(symbols,expiration):
    
    '''
    The function create a dataframe with key information from the chain, sorted the data
    by the deltaFormula variable and send the data to the optionScreener worksheet
    Parameters:
        symbols: lists of symbols to get the chains by their expiration date
        expiration: date of expiry date of the contracts for a specific symbol 
        such as SPY or for many symbols. Sometimes symbols have the same expiration
        date. 
        
    Returns:
        optionChain_df: data frame with contracts information for the expiration 
        date that is passed as parameter(expiration). The dataframe can contain
        contracts of many symbols.
    '''
    
   
    contracts =  r.find_options_for_list_of_stocks_by_expiration_date(symbols,expiration)

    currentDate = str(datetime.datetime.now().date())
    option_chain = []
    
    # Create these three dictionaries for tracking open Interest for calls and puts
    # by symbol and Implied Volatility by symbols. The Open interest will  be useful
    # for calculate the call/put ratio and the Implied Volatility to calculate the mean
    # of the Implied Volatility for each expiration date.
    callsOI = {}
    putsOI = {}
    ImpVol = {}
      
    for contract in contracts:
        
        try:    
            symbol = contract['chain_symbol']
            optionContract = symbol + contract['expiration_date'].replace('-','')[2:] + contract['type'][0].upper() + contract['strike_price'].replace('.','')
            adjPrice = float(contract['adjusted_mark_price'])
            askPrice = contract['ask_price']
            bidPrice = contract['bid_price']
            askSize = contract['ask_size']
            bidSize = contract['bid_size']
               
            if symbol not in callsOI.keys():
                callsOI[symbol] = 0
                
            if symbol not in putsOI.keys():
                putsOI[symbol] = 0
            
            if symbol not in ImpVol.keys():
                ImpVol[symbol] = 0
            
            expiry = contract['expiration_date']
            
            prevClose = contract['previous_close_price']
            lastTradePrice = contract['last_trade_price']
    
            underlying = float(r.get_latest_price(symbol)[0])
            
            if contract['delta'] != None:
                delta = float(contract['delta'])
                deltaFormula = 100 * (1-abs(delta))
            else:
                delta = 0   # If the contract doesn't have delta values, fill 
                            # this field with zero, in order to have all numeric values
                deltaFormula = 0 # in this column that allow to sort the data.
        
            if contract['type'] == 'call':
                intrinsicValue = underlying - float(contract['strike_price'])
                callsOI[symbol] += float(contract['open_interest'])
                
            elif contract['type'] == 'put':
                intrinsicValue = float(contract['strike_price']) - underlying
                putsOI[symbol] += float(contract['open_interest'])
                
            if contract['implied_volatility'] != None:
                IV = float(contract['implied_volatility'])
                ImpVol[symbol] += float(contract['implied_volatility'])
            else:
                IV = 0
               
            volume = contract['volume']
        
        
            info = {'Expiration':expiry, 'Date': currentDate,'contract':optionContract,'adjPrice':adjPrice,'askPrice':askPrice, 
                    'bidPrice':bidPrice,'askSize': askSize, 'bidSize':bidSize,
                    'prevClose':prevClose, 'lastTradePrice': lastTradePrice, 
                    'ImpliedVolatility': IV, 'delta': delta, 'deltaFormula':deltaFormula,
                    'volume':volume, 'UnderlyingPrice': underlying, 
                     'IntrinsicValue': intrinsicValue}
            
            option_chain.append(info)
           # print(info)
            
        except Exception as e:
            print(e)   
            print('For contract {} cannot get information'.format(optionContract))
            #continue

#        time.sleep(1)
     #   print('Getting chain for {} date {}'.format(symbol,expiration))
        
    optionChain_df = pd.DataFrame(option_chain)       
    
    columns = ['Expiration','contract', 'adjPrice','askPrice', 'bidPrice', 'askSize','bidSize', 'prevClose',
               'lastTradePrice', 'ImpliedVolatility', 'delta','deltaFormula',
               'volume','UnderlyingPrice','IntrinsicValue','Date']
    
    print(optionChain_df)
    optionChain_df.sort_values('deltaFormula',ascending=False,inplace=True)
    
    optionChain_df = optionChain_df[columns]
    
    index = 3
    for k, value in callsOI.items():
        print('Add OI for calls of {} for symbol {}'.format(value,k))    
        PCR.insert_row([expiration,k,value],index)
        index +=1
        time.sleep(2)
            
    for k, value in putsOI.items():
        print('Add OI puts of {}  for symbol {}'.format(value,k))
        PCR.insert_row([expiration,k,value],index)
        index += 1
        time.sleep(2)
            
    for k, value in ImpVol.items():
        print('Add IV sum of  {}  for symbol {}'.format(value,k))
        PCR.insert_row([expiration,k,value],index)
        index += 1
        
        time.sleep(2)
 
   
    #gd.set_with_dataframe(optionScreener, optionChain_df)
    
    
    #index = 2
    #optionScreener.insert_row([expiration],1)
    #optionScreener.insert_row(info,index)
    
       
            
        
        #option_data.append({'adjustedPrice':adjPrice,'askPrice':askPrice,'bidPrice':bidPrice,
        #                'askSize':askSize,'bidSize':bidSize, 'previousClose':prevClose,
        #                'lastTradePrice':lastTradePrice, 'delta':delta, 'gamma':gamma,
        #                'theta':theta,'vega':vega, 'type':type_, 'strike':strike,
        #                'volume':volume,'IV':IV})

   # option_df = pd.DataFrame(option_data)    
    
    
    #writer = ExcelWriter('SYY.xlsx')
    ##option_df.to_excel(writer,'Sheet5') 
    #writer.save()
    
    return optionChain_df, callsOI, putsOI, ImpVol
  
   
if __name__ == '__main__':
    
    master_ChainList = []
    syms = ['SPX','RUT','NDX','SPY','IWM','TNA','GLD']
    
    OpenInterestCalls = []
    OpenInterestPuts = []
    ImpliedVolatility = []
    
    expiryDates,symbols,symbolDates = expirationDates(syms)
    
    print('Structure of chains to load on the google sheet is %s' % symbolDates)
    
    for date in expiryDates:        
        
        print('Processing option chain with date {}'.format(date))
        
        Chain_df , OICalls, OIPuts, ImpVol  = contracts_by_expiration(symbols,date)
        
       
        master_ChainList.append(Chain_df)
        OpenInterestCalls.append({str(date):OICalls})
        OpenInterestPuts.append({str(date):OIPuts})
        ImpliedVolatility.append({str(date):ImpVol})
        
    allchains = pd.concat(master_ChainList)
    

    allchains['delta'] = allchains['delta'].astype(float)    
    # Filter all contracts on the dataframe with delta higher than 0.2
    allchains = allchains[allchains['delta'] <= 0.2]
    
    
    
    allchains.sort_values('ImpliedVolatility',inplace=True,ascending=False)
    
    gd.set_with_dataframe(optionScreener, allchains)
        
columns = ['Contract','AdjPrice','askPrice','bidPrice','askSize','bidSize','prevClose',
           'lastTradePrice','IV','delta','DeltaFormula','volume','currentDate']


#dir(holdings)
#cell_list = optionScreener.range('A2:M2')
#cell_list
#for i in range(0,len(cell_list)):
#   cell_list[i].value = columns[i]
    
#cell_list
#optionScreener.update_cells(cell_list)


columns = dates
cell_list = PCR.range('B2:E2')
cell_list
for i in range(0,len(cell_list)):
   cell_list[i].value = columns[i]
    
cell_list
PCR.update_cells(cell_list)

