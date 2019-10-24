# -*- coding: utf-8 -*-
"""
Created on Sun Oct  6 17:42:51 2019

@author: Nicolas
"""
import datetime
import robin_stocks

r = robin_stocks
r.login("jancsikeresztes@gmail.com","BotTrading2019")


##### Function to calculate derivative sign at tt minutes after market open

class SymbolDerivative():
    
    def __init__(self,minutes,symbol):
        
        self.minutes = minutes
        self.symbol = symbol
        self.warmUpPrices = []
        self.marketOpen = None
        
    def derivative(self):
        if self.marketOpen == True:
            for minute in self.minutes:
                price = r.get_latest_price(self.symbol)
                self.warmUpPrices.append(price)


    def markeOpen(self,):
    
        time = datetime.datetime.now()
        if time.hour == 9 and time.minute == 30:
            self.marketOpen = True
            
        return self.markeOpen
    
    
if __name__ == '__main__':
    der = SymbolDerivative()
    
    time = datetime.datetime.now()
    


symbols = ["TSLA", "BABA", "EAT", "TWTR", "TTNP", "SBUX", "BAC", "DIS", "STM", "ACB", "GREK", "MSFT",
           "AAPL", "F", "NVDA", "FB", "NFLX",'CGC','TXN','IIPR','MBOT','CRON','VSH', 'USNA',  'SPWR',
          'BGS', 'QRVO', 'CGNX', 'AMD', 'MYGN', 'DLR', 'ORA', 'SAND', 'XLNX', 'CDXS', 'SPY', 'NBEV',
           'WORK','EPD','VNOM','GLOP', 'CRNT', 'TORC', 'AMBA',"MU","WFC","CHK","SNAP","GE","AUY",
           "ECA","FCX","T","ZNGA","RIG","AABA","KGC","ROKU","MDR","SWN","HPQ","LVS","NLY","GPRO","SIRI","BHGE",
           "VER","HAL","GOLD","MRO","RRC","CSCO","BK","PFE","X","CPE","MPC","INTC","AKS","CMCS_A",
           "ORCL","M","NGD","BB","DNR","SQ","PCG","BSX","HPE","BTG","HST","C","AMAT","CLF","SLB","WU",
           "OAS","NEM","JPM","AR","MO","XOM","ATVI","VZ","MRK","GILD","KO","EMR","ABBV","MDLZ","NKE",
           "WDC","TJX","CVS","BBT","QCOM","DAL","PGR","COP","PM","USB","FSLR","SSNC","HES",
           "AFL","ZEN","LUV","WBA","EOG","TMUS","BAM","ABT","AIG","SO","LYB","SWKS","CMS","VLO","EXAS",
           "OKTA","CTSH","STI","QSR","ICE","LYV","STX","DOCU","EVRG","DELL","SGEN","FTV","DHI","INFO",
           "XEL","BMRN","TER","AEM","BAX","LEN","AEP","D","BLL","CSX","GH","EIX","AVLR","DD",
           "ETSY","CHD","MTCH","DUK","CVNA","PLD","PRU","ALB","CXO","EA","HFC","XPO","BBY","TDOC","XRAY",
           "GIS","APH","OC","FANG","LITE","CERN","TNDM","GRUB","UAL","NUE","STT","DVA","BLUE","PEG","ALXN"
           "TSN","ESTC","CTXS","VFC","A","AME","SYY","WEC","WELL","WCN","KEYS","TAP","NTAP","TSCO","NCLH",
           "ES","ABC","SEDG","MNST","BNS","ETN","K","PAYX","TD","REGN","PCTY","NOMD","VRSK","TRP","GDDY","RSG","EHTH","PLNT","HLT",
           "OKE","MCHP","TRU","OLLI","VNO","FND","PCAR","FTNT","KMX","ED","IONS","VTR","DDS","IRBT","SPB",
           "CDNS","OMC","LNG","NEWR","CCK","CBRE","HIG","EVBG","RHI","MMS","IPHI","O","LNC","SHAK"]
    
    