#Author:  Joshua Campbell
#Python:  version 2.7.3
#Purpose: Experiment with Genetic Algorithms to find solutions to problems, in this case
#         to find suitable behaviour buying/selling stocks listed on NASDAQ given 3 months
#         historical data. This is for my learning purposes only, so low expectations would
#         be advisable in regard to effectiveness or implementation. This is new ground for me


import urllib2
import mysql.connector
from mysql.connector import errorcode
#import sqlite3

#
# get_page retrieves the 3 month data for all stocks and saves them to files.
#

def get_page(symbols):
     results=[]
     for stock in symbols:
          try:
               url="http://www.nasdaq.com/symbol/"+stock+"/historical"
               response=urllib2.urlopen(url)
               page=response.read().replace('\r\n','').replace(' ','')
               tablestart=page.find("<tbody>")
               page=page[tablestart:]
               tableend=page.find("</tbody>")
               table=page[:tableend]
               table.replace('\n',"")
               element=[stock, table]
               if element[1] != '':
                    filename=element[0]+".txt"
                    file=open(filename, 'w')
                    file.write(element[1])
                    file.close()
                    results.append(filename)
          except urllib2.HTTPError as e:
               print "HTTP Error: " + e.code
               print e.read()
          except:
               print "unhandled error"
     return results
#
# get_symbols extracts the stock symbol from the listing pass in
#             currently designd for nasdaqlisted.txt

def get_symbols(listing):
    file=open(listing, 'r')
    allsymbols=[]
    line=file.readline() #remove the first line and trash it. 
    for line in file:
          delim=line.find('|')
          symbol=line[:delim]
          allsymbols.append(symbol)
    allsymbols.pop() #removes last line which is garbage
    file.close()
    return allsymbols
     
     
def create_database(cursor):
     try:
          cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
     except mysql.connector.Error as err:
          print("Failed creating database: {}".format(err))
          exit(1)
          
#
# create_db recieves a file containing the names of all the textfiles from
# get_page

def create_db(all_files):
     file=open(all_files,'r')
     filenames=[]
     symbols=[]
     symbols=get_symbols('nasdaqlisted.txt')
     symbolidx=0
     DB_NAME = 'stocksdb'
     TABLES = {}
     TABLES['stocks'] = (
          "CREATE TABLE IF NOT EXISTS stocks ("
          "     symbol VARCHAR(4) NOT NULL,"
          "     date VARCHAR(10) NOT NULL,"
          "     open DECIMAL(5,2) NOT NULL,"
          "     high DECIMAL(5,2) NOT NULL,"
          "     low DECIMAL(5,2) NOT NULL,"
          "     close DECIMAL(5,2) NOT NULL,"
          "     volume DECIMAL(5,2) NOT NULL,"
          "     PRIMARY KEY (symbol, date)"
          ") ENGINE=InnoDB")
          
     cnx = mysql.connector.connect(user='root', password='josh2099', port=8888)
     cursor = cnx.cursor()
          
     try:
          cnx.database = DB_NAME
     except mysql.connector.Error as err:
          if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
               print("Invalid login/password")
          elif err.errno == errorcode.ER_BAD_DB_ERROR:
               create_database(cursor)
               cnx.database = DB_NAME
          else:
               print(err)
               exit(1)
               
     for name, dd1 in TABLES.iteritems():
          try:
               print("Creating table {}: ".format(name))
               cursor.execute(dd1)
          except mysql.connector.Error as err:
               if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("Table already exists.")
               else:
                    print(err.msg)


     add_stock = ("INSERT IGNORE INTO stocks (symbol, date, open, high, low, close, volume) VALUES (%s, %s, %s, %s, %s, %s, %s)")
     for line in file:
         filenames.append(line.rstrip())
     file.close()

     for stock in filenames:
          file=open(stock,'r')
          table=file.read()
          while table.find("<!--TT-->") >= 0:
               table=table[table.find("<!--TT-->")+9:]
               date=table[:table.find('<')]
               table=table[table.find('<')+9:]
               openprice=table[:table.find('<')]
               table=table[table.find('<')+9:]
               high=table[:table.find('<')]
               table=table[table.find('<')+9:]
               low=table[:table.find('<')]
               table=table[table.find('<')+9:]
               closelast=table[:table.find('<')]
               table=table[table.find('<')+9:]
               volume=table[:table.find('<')] 
               table=table[table.find('<')+9:]
               t=(symbols[symbolidx], date, openprice, high, low, closelast, volume,)
               cursor.execute(add_stock, t)
          symbolidx=symbolidx+1
		
     cnx.commit()
     cursor.close()
     cnx.close()


#
# print_db() prints all rows in the database passed to it
#


# create_db("filelist.txt")




#############################################################################################
# EVERYTHING ABOVE THIS COMMENT IS FOR BUILDING THE DATABASE, ALL ANALYTICAL CODE IS BELOW. #
#############################################################################################


# 1. Initialize
# 2. Evaluate
# 3. Selection
# 4. Crossover
# 5. Mutation
# 6. Repeat!


class Individual:
    acctbalance=0       #account balance, looking to maximize this in the end
    diversitylevel=0    #level of diversity when buying, 0 being least diverse, 255 being most diverse
    losstolerance=0     #percentage of loss allowed before selling, 1-100
    gaintolerance=0     #percentage of gain allowed before selling, 1-100
    buyondecline=0      #whether or not to buy a stock that is currently decreasing, 0 is false, 1 is true
    buyonincline=0      #whether or not to buy a stock that is currently decreasing, 0 is false, 1 is true
    percenttoreinvest=0 #percentage of returns to reinvest, 1-100
    amountinvested=0    #total amount of money in stocks currently owned
    genelength=0        #length of DNA
    owned={}            #dictionary containing the symbols of all purchased stock, and amount owned
    

    def __init__(self, acctbalance, diversitylevel, losstolerance, gaintolerance, ondecline, onincline, pctreinvest):
        self.acctbalance=acctbalance
        self.diversitylevel=diversitylevel
        self.losstolerance=losstolerance
        self.gaintolerance=gaintolerance
        self.owned={}
        self.buyondecline=ondecline
        self.buyonincline=onincline
        self.amountinvested=0
        self.percenttoreinvest=pctreinvest

    # def buy(self, symbol, price, amount):
        # if symbol not in owned:
            # self.owned.update((symbol:amount))
        # else:
            # if self.acctbalance>=(amount*price):
                # self.owned[symbol]=self.owned.get(symbol)+amount
                # self.acctbalance=self.acctbalance-(amount*price)
            # else: #buy as many as possible without going negative
                # self.owned[symbol]=self.owned.get(symbol)+(self.acctbalance/price)
                # self.acctbalance=self.acctbalance-((self.acctbalance/price)*price)

    # def sell(self, symbol, price, amount):
        # if symbol in owned:
            # if self.owned.get(symbol)>=amount:
                # self.owned[symbol]=self.owned.get(symbol)-amount
                # self.acctbalance=self.acctbalance+(amount*price)
                # if self.owned.get(symbol)==0:
                    # del self.owned[symbol]
            # else:#sells all of that stock since less was owned than 'amount'
                # self.acctbalance=self.acctbalance+(self.owned.get(symbol)*price)    
                # del self.owned[symbol]
                
    # def get_dna(self):
        # DNA='{0:08b}'.format(diversitylevel)+'{0:08b}'.format(losstolerance)+'{0:08b}'.format(gaintolerance)+self.buyondecline+self.buyonincline+'{0:08b}'.format(self.percenttoreinvest)
        # return DNA
    
    # def get_balance(self):
        # return self.acctbalance

    # def to_buy(self, symbol):
        # #for each stock
        # #read todays posting and update memory
        

# def fitness(Individual, Best):
    
