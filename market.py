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

tresholdPercentile=0.5
stepper=1000*60   #minute stepper

#################   Config   ###################


#open config file to find out address
with open("config.json") as urlfile:
    configbefore=urlfile.read()
    configafter=json.loads(configbefore)

r = requests.get(configafter['url'])
marketPrice = json.loads(r.text, object_pairs_hook=OrderedDict)


print("Market Prices retrieved from myjson.com with "+str(len(marketPrice))+" items")
lastestTimestamp = float(list(marketPrice["logs"].keys())[-1])/1000.0
latestDatetime = datetime.datetime.fromtimestamp(lastestTimestamp, tzlocal())
print("Latest Price: "+str(latestDatetime.strftime("%I:%M %p %z   %d-%b-%Y")))
sys.stdout.write("Press any key to continue...")
input()
print()
print()

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
    print("Analysis for "+item)
    print("============="+"="*len(item))
    print("Data count: "+str(len(times)))

    stats=DescrStatsW(prices, weights)
    print("Weighted Average Price: "+"{:,.2f}".format(stats.mean))
    print("Weighted Stdev: "+"{:,.2f}".format(stats.std))
    print()
    print("Percentiles:")
    print("5% : "+"{:,.2f}".format(stats.quantile(0.05,False)[0]))
    print("15% : "+"{:,.2f}".format(stats.quantile(0.15,False)[0]))
    print("50% : "+"{:,.2f}".format(stats.quantile(0.50,False)[0]))
    print("85% : "+"{:,.2f}".format(stats.quantile(0.85,False)[0]))
    print("95% : "+"{:,.2f}".format(stats.quantile(0.95,False)[0]))
    print()
    print("Current Price        : "+"{:,.2f}".format(prices[-1]))
    print("Potential High Price : "+"{:,.2f}".format(stats.quantile(tresholdPercentile,False)[0]))
    print("Potential Profit     : "+"{:,.2f}".format(stats.quantile(tresholdPercentile,False)[0]-round(prices[-1],2)))
    print("\n\n")
    profits[item]=round(stats.quantile(tresholdPercentile,False)[0],2)-round(prices[-1],2)
    profitsPercent[item]=(round(stats.quantile(tresholdPercentile,False)[0],2)-round(prices[-1],2))/prices[-1]

print("FINAL ANALYSIS")
print("==============")

profitsPercent=OrderedDict(sorted(profitsPercent.items(), key=itemgetter(1), reverse=True))
for item in profitsPercent:
    print(item+" "*(30-len(item))+":"+"{:.2f}".format(profitsPercent[item]*100)+"% ("+"{:,.2f}".format(profits[item])+")")

