#!/usr/bin/env python3
#
#
# Diamond Hunt Marketplace Analyzer 
# Author: Samuel Pua (kahkin@gmail.com)
#
##############################################

import json
import requests
import numpy
import sys
from statsmodels.stats.weightstats import DescrStatsW
from collections import OrderedDict
from operator import itemgetter
import datetime
from dateutil.tz import tzlocal

#################   Config   ###################

latestFile="latest.txt"

tresholdPercentile=0.5
stepper=1000*60   #minute stepper
woodList=["logs", "oakLogs", "willowLogs", "mapleLogs", "stardustLogs", "strangeLogs", "ancientLogs"]
energyList=[1,2,5,10,20,30,50]

################   Functions   ##################

def allPrint(f, stuff=""):
    print(stuff)
    f.write(stuff+"\n")


##############   Start Analysis   ################

#open config file to find out address
with open("config.json") as urlfile:
    configbefore=urlfile.read()
    configafter=json.loads(configbefore)

#logs latest run
latestFileHandler=open(latestFile, "w")

r = requests.get(configafter['url'])
marketPrice = json.loads(r.text, object_pairs_hook=OrderedDict)


allPrint(latestFileHandler,"Market Prices retrieved from myjson.com with "+str(len(marketPrice))+" items")
lastestTimestamp = float(list(marketPrice["logs"].keys())[-1])/1000.0
latestDatetime = datetime.datetime.fromtimestamp(lastestTimestamp, tzlocal())
allPrint(latestFileHandler,"Latest Price: "+str(latestDatetime.strftime("%I:%M %p %z   %d-%b-%Y")))
sys.stdout.write("Press any key to continue...")
input()
allPrint(latestFileHandler,)
allPrint(latestFileHandler,)

profits=OrderedDict()
profitsPercent=OrderedDict()
for item in marketPrice:
    times=[]
    prices=[]
    weights=[]

    for time in marketPrice[item]:
        if len(times)==0:
            prevtime=time
            times.append(float(time))
            prices.append(float(marketPrice[item][time]))
        else:
            while float(time)>times[-1]+stepper:
                totalTimeDiff=float(time)-float(prevtime)
                timePassed=(times[-1]+stepper-float(prevtime)) / totalTimeDiff

                times.append(times[-1]+stepper)
                newPrice=marketPrice[item][prevtime]+timePassed*(float(marketPrice[item][time])-float(marketPrice[item][prevtime]))
                prices.append(newPrice)

                #assigning weights based on 0.5 before + 0.5 after
                if len(times)==2:
                    weights.append(1)  #first weight is 0.5 of 1st to 2nd
                if len(times)>2:
                    weights.append(1)  #middle is next minus beore * 0.5

            #adding real records
            times.append(float(time))
            prices.append(float(marketPrice[item][time]))

            #registering actual time change
            prevtime=time

            #assigning weights based on 0.5 before + 0.5 after
            if len(times)==2:
                weights.append(1)  #first weight is 0.5 of 1st to 2nd
            if len(times)>2:
                weights.append(1)  #middle is next minus beore * 0.5

    #add last weight
    weights.append(1)  #last is last minues before * 0.5

    #start analysis
    allPrint(latestFileHandler,"Analysis for "+item)
    allPrint(latestFileHandler,"============="+"="*len(item))
    allPrint(latestFileHandler,"Data count: "+str(len(times)))

    stats=DescrStatsW(prices, weights)
    allPrint(latestFileHandler,"Weighted Average Price: "+"{:,.2f}".format(stats.mean))
    allPrint(latestFileHandler,"Weighted Stdev: "+"{:,.2f}".format(stats.std))
    allPrint(latestFileHandler,)
    allPrint(latestFileHandler,"Percentiles:")
    allPrint(latestFileHandler,"5% : "+"{:,.2f}".format(stats.quantile(0.05,False)[0]))
    allPrint(latestFileHandler,"15% : "+"{:,.2f}".format(stats.quantile(0.15,False)[0]))
    allPrint(latestFileHandler,"50% : "+"{:,.2f}".format(stats.quantile(0.50,False)[0]))
    allPrint(latestFileHandler,"85% : "+"{:,.2f}".format(stats.quantile(0.85,False)[0]))
    allPrint(latestFileHandler,"95% : "+"{:,.2f}".format(stats.quantile(0.95,False)[0]))
    allPrint(latestFileHandler,)
    profits[item]=round(stats.quantile(tresholdPercentile,False)[0],2)-round(prices[-1],2)
    profitsPercent[item]=(round(stats.quantile(tresholdPercentile,False)[0],2)-round(prices[-1],2))/prices[-1]
    allPrint(latestFileHandler,"Current Price        : "+"{:,.2f}".format(prices[-1]))
    allPrint(latestFileHandler,"Potential High Price : "+"{:,.2f}".format(stats.quantile(tresholdPercentile,False)[0]))
    allPrint(latestFileHandler,"Potential Profit     : "+"{:,.2f}".format(profits[item])+"  ("+"{:,.2f}".format(profitsPercent[item]*100)+"%)")
    allPrint(latestFileHandler,"\n\n")


allPrint(latestFileHandler,"Profit Analysis") 
allPrint(latestFileHandler,"===============")

profitsPercent=OrderedDict(sorted(profitsPercent.items(), key=itemgetter(1), reverse=True))
for item in profitsPercent:
    allPrint(latestFileHandler,item+" "*(30-len(item))+":"+"{:.2f}".format(profitsPercent[item]*100)+"% ("+"{:,.2f}".format(profits[item])+")")

allPrint(latestFileHandler,"\n")

allPrint(latestFileHandler,"Wood Analysis")
allPrint(latestFileHandler,"=============")

for i in range(len(woodList)):
    output=woodList[i]
    output=output+": "
    woodPrice=list(marketPrice[woodList[i]].values())[-1]
    output=output+"{:,.2f}".format(woodPrice)+" ("
    output=output+"{:,.2f}".format(woodPrice / energyList[i])+" coins per energy)"
    allPrint(latestFileHandler,output)

allPrint(latestFileHandler,)

################ Cleaning Up ################
latestFileHandler.close()
