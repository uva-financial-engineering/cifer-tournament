#This code generates the stock and option prices seen in the IEEE-CIFER 2014 Competition
#This code is available to be use and modified for non-profit and academic work
#Please use the following Cititation in any publication
# Hayes, R. Tepsuporn, S. Chaidarun, N. Grazioli, S. Beling, P. & Scherer W. IEEE-CIRFER 2014 Comepetition Price Generator
import sys
import os
import copy
import datetime
import math
import random
import re
from datetime import date, timedelta

def main():
    inputFile = open("Input File.csv")

    #Variables needed to generate stockMarket Prices
    Stock = [] # stock names
    Sectors =[] #sector each stock belongs
    betas = [] # beta of each stock
    Volatility = [] # volatility of each stock
    currentPrice = [] # starting/current price of stock
    spPrice =[] #S&P 500 price path
    currentDate = datetime.date(2013,11,22) # start date of simulation (assumes weekday)
    endDate = datetime.date(2013,11,22) # end date of simulation
    expDate = datetime.date(2013,11,22) # expiration date of options
    i = 0

    #Initialize Variables from input file
    for line in inputFile:
        if i == 0:
            line.replace('\n','')
            temp = line.split(',')
            temp.pop(0)
            for name in temp:
                Stock.append(name.replace('\n',''))
        elif i == 1:
            line.replace('\n','')
            temp = line.split(',')
            temp.pop(0)
            for sector in temp:
                Sectors.append(sector.replace('\n',''))
        elif i == 2:
            line.replace('\n','')
            temp = line.split(',')
            temp.pop(0)
            for beta in temp:
                betas.append(beta.replace('\n',''))
        elif i == 3:
            line.replace('\n','')
            temp = line.split(',')
            temp.pop(0)
            for vol in temp:
                Volatility.append(vol.replace('\n',''))
        elif i == 4:
            line.replace('\n','')
            temp = line.split(',')
            temp.pop(0)
            for price in temp:
                currentPrice.append(price.replace('\n',''))
        elif i == 5:
            line.replace('\n','')
            temp = line.split(',')
            temp.pop(0)
            for price in temp:
                spPrice.append(price.replace('\n',''))
        elif i == 6:
            line.replace('\n','')
            temp = line.split(',')
            date= temp[1].split('/')
            currentDate = datetime.date(int(date[2]),int(date[0]),int(date[1]))
        elif i == 7:
            line.replace('\n','')
            temp = line.split(',')
            date= temp[1].split('/')
            endDate = datetime.date(int(date[2]),int(date[0]),int(date[1]))
        elif i ==8:
            line.replace('\n','')
            temp = line.split(',')
            date= temp[1].split('/')
            expDate = datetime.date(int(date[2]),int(date[0]),int(date[1]))
        i+=1    

    inputFile.close()
    #initializing the first stock prices
    stockPrices='Date, Stock Ticker, Sector, Bid, Ask\n'
    for x in range(0, len(Stock)):
        stockPrices += str(currentDate) +','+ Stock[x] +',' + Sectors[x] + ','+currentPrice[x]+','+str(float(currentPrice[x])+0.01)+'\n'

   
    z = 1
    while z < len(spPrice) and currentDate<= endDate:

        #augments historical price by uniform random distribution [-2%,2%]
        priceAugmentor =0.98+ random.uniform(0,0.04)
        spPrice[z] = str(float(spPrice[z])*priceAugmentor)

        #increments date making sure it is a weekday 5 = sat & 6 = Sun
        currentDate = currentDate+timedelta(days=1)
        while currentDate.weekday() >4:
            currentDate = currentDate+timedelta(days=1)

        #calculates the new stock price using beta and adding unifrom noise   [-2%,2%]
        percentageMove = (float(spPrice[z]) - float(spPrice[z-1]))/float(spPrice[z-1])
        for x in range(0, len(Stock)):
            beta = float(betas[x])
            priceJump = 1 + (beta * percentageMove)
            currentPrice[x]=str(float(currentPrice[x]) * priceJump*(1 + random.gauss(0,float(Volatility[x]))))
            stockPrices += str(currentDate) +','+ Stock[x] +',' + Sectors[x] + ','+currentPrice[x]+','+str(round(float(currentPrice[x])+0.01,2))+'\n'
        z+=1   
    #Prints out the stockmarket values 
    with open('stockMarket.csv',"w") as out_file:
        out_file.write(stockPrices)    

    

    #reads from inputFile again
    inputFile = open("Input File.csv")
    i=0
    currentPrice=[]
    #Initialize Variables from input file setting currentDate and currentPrices to starting values
    for line in inputFile:
        if i == 4:
            line.replace('\n','')
            temp = line.split(',')
            temp.pop(0)
            for price in temp:
                currentPrice.append(price.replace('\n',''))
        elif i == 6:
            line.replace('\n','')
            temp = line.split(',')
            date= temp[1].split('/')
            currentDate = datetime.date(int(date[2]),int(date[0]),int(date[1]))
        i+=1        
    inputFile.close()

    i=0
    #Genearate strike prices: if starting price <= $15 than options prices are incremented by $0.5 else $1
    StrikePrice =[]
    
    for price in currentPrice:
        p = round(float(price),0)
        mod = 0
        if p <= 15:
            mod = 0.5
        else:
            mod = 1
        i = -4
        while i <= 4:
            StrikePrice.append(p+(i*mod))
            i+=1
    #generating option Market Prices
    stockPriceFile = open("stockMarket.csv")
    optionMarketOutput ="Date,Sector, Name, Type, Strike Price, Bid, Ask\n"
    #counters to navigate stockMarket Files and relevant list
    i = 0
    z = 0
    N = 9
    increment = 9
    switchPoint = 4 #switch from call options to put options used on strikePice list
    cashInterest = 0.01
    skippedFirstLine = False

    #iteratres through stock price files
    for line in stockPriceFile:
        if skippedFirstLine:
            line.replace('\n','')
            lineSeperated = line.split(',')

            #Finds the time till expiration date
            date = lineSeperated[0].split('-')
            currentDate = datetime.date(int(date[0]),int(date[1]),int(date[2]))
            tdelta = expDate - currentDate
            time = float(tdelta.days)/365

            #gets Stock Name and volatility
            stockName = Stock[i]
            stockVol = float(Volatility[i])

            #gets Stocks Current Price and sector
            curPrice = float(lineSeperated[3])
            stockSector = lineSeperated[2]
            #calculates the option Prices and adds them to the output file
            while z < N:
                if z <= switchPoint:
                    cPrice = round(callPrice(curPrice, StrikePrice[z], cashInterest, time, stockVol),2)
                    if cPrice > 0:
                        optionMarketOutput+= str(currentDate)+','+stockSector+','+stockName+',Call,'+str(StrikePrice[z])+','+str(cPrice)+','+str(cPrice+0.01)+'\n'
                if z>= switchPoint:
                    pPrice = round(putPrice(curPrice, StrikePrice[z], cashInterest, time, stockVol),2)
                    if pPrice > 0:
                        optionMarketOutput+= str(currentDate)+','+stockSector+','+stockName+',Put,'+str(StrikePrice[z])+','+str(pPrice)+','+str(pPrice+0.01)+'\n'
                z+=1
            i+=1
            switchPoint += increment
            N+= increment
            if i >= len(Stock):
                i = 0
                z = 0
                N= 9
                switchPoint = 4
        else:
            skippedFirstLine = True

    with open('optionMarket.csv',"w") as out_file:
        out_file.write(optionMarketOutput) 
    
    pass
# generates option prices uniform random noise 
def callPrice (CurrentPrice,Strike,interst, Time, volatility):

    d = (math.log(CurrentPrice/Strike)+(interst + math.pow(volatility,2)/2)*Time)/(volatility *math.sqrt(Time))
    m = d - (volatility *math.sqrt(Time))
    p= CurrentPrice*(float(1+math.erf(d/math.sqrt(2)))/2) - Strike*math.exp(-interst*Time)* (float(1+math.erf(m/math.sqrt(2)))/2)
    return p*(0.98+ random.uniform(0,0.04))

def putPrice (CurrentPrice,Strike,interst, Time, volatility):

    d = (math.log(CurrentPrice/Strike)+(interst + math.pow(volatility,2)/2)*Time)/(volatility *math.sqrt(Time))
    m = d - (volatility *math.sqrt(Time))
    p = Strike*math.exp(-interst*Time)* (float(1+math.erf(-m/math.sqrt(2)))/2) - CurrentPrice*(float(1+math.erf(-d/math.sqrt(2)))/2)
    return p *(0.98+ random.uniform(0,0.04))

if __name__ == "__main__":
    main()
