#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
import sys, importlib

sys.path.append("/home/python")
importlib.reload(sys)

import time, configparser, threading
import common.OKClient as OKClient

# read config
config = configparser.ConfigParser()
config.read("config.ini")

# getConfig
cross = config.get("strategy", "cross")
ma1 = cross.split("|")[0]
if ma1 != "current":
    ma1 = int(ma1)
ma2 = cross.split("|")[1]
if ma2 != "current":
    ma2 = int(ma2)

type = config.get("kline", "type")
shift = float(config.get("kline", "shift"))
symbol = config.get("trade", "symbol")
transaction = float(config.get("trade", "transaction"))

# global variable
trendBak = ""
transCountBak = int(config.get("statis", "transcount"))
transMode = "minus"
current = 0
currentList = []
orderInfo = OKClient.orderInfo
orderDiff = OKClient.orderDiff
tradeRemain = 0


def calAvgReward():
    global tradeRemain
    orderBuyList = list(filter(lambda orderIn: orderIn["type"] == 'buy', OKClient.orderList))
    orderSellList = list(filter(lambda orderIn: orderIn["type"] == 'sell', OKClient.orderList))
    buyAmount = 0
    buyCost = 0
    sellAmount = 0
    sellReward = 0
    for order in orderBuyList:
        buyAmount += order["deal_amount"]
        buyCost += order["deal_amount"] * order["avg_price"]
    buyAvg = buyCost / buyAmount
    for order in orderSellList:
        sellAmount += order["deal_amount"]
        sellReward += order["deal_amount"] * order["avg_price"]
    tradeRemain = buyAmount - sellAmount
    sellAvg = sellReward / sellAmount
    avgReward = round(sellAvg - buyAvg, 2)
    config.read("config.ini")
    config.set("statis", "avgreward", str(round(float(config.get("statis", "avgreward")) + avgReward, 2)))
    config.set("statis", "reward", str(round(float(config.get("statis", "reward")) + sellReward - buyCost, 2)))
    config.set("statis", "transcount", str(int(config.get("statis", "transcount")) + 1))
    fp = open("config.ini", "w")
    config.write(fp)
    OKClient.writeLog(' '.join(
        ["avgPriceDiff:", str(avgReward), "transactionReward:",
         str(round(sellReward - buyCost, 2))]))


def getAmount():
    orderBuyList = list(filter(lambda orderIn: orderIn["type"] == 'buy', OKClient.orderList))
    totalAmount = 0
    for order in orderBuyList:
        totalAmount += order["deal_amount"]
    if totalAmount != 0:
        totalAmount += tradeRemain
    return totalAmount


def orderProcess():
    global orderInfo, current, symbol
    amount = OKClient.getUnhandledAmount()
    status = OKClient.trade(symbol, orderInfo["type"], amount, current)
    # dealed or part dealed
    if status != -2:
        OKClient.setTransaction("minus")
        OKClient.writeLog()
    if status == 2:
        if orderInfo["type"] == "sell":
            print(OKClient.orderList)
            calAvgReward()
    elif orderInfo["dealAmount"] != 0:
        orderProcess()


def getMA(param):
    ms = int(time.time() * 1000)
    if type == "15min":
        ms -= param * 15 * 60 * 1000
    elif type == "5min":
        ms -= param * 5 * 60 * 1000
    elif type == "1min":
        ms -= param * 1 * 60 * 1000
    data = OKClient.okcoinSpot.klines(symbol, type, param, ms)
    ma = 0
    # if len(data) != param:
    #     raise Exception("waiting data...")
    for line in data:
        ma += line[4]
    return round(ma / len(data), 2)


def maXVsMaX():
    global trendBak, shift
    maU = getMA(ma1)
    maL = getMA(ma2)
    diff = maU - maL
    if diff > shift:
        trend = "buy"
    else:
        trend = "sell"
    if trendBak != "" and trendBak != trend:
        # sendEmail("trend changed:" + str(maU) + " VS " + str(maL))
        OKClient.setOrderInfo(symbol, trend, getAmount(), transaction)
        if trend == "buy":
            OKClient.orderList = []
            OKClient.writeLog("-----------------------------------------------------------------------")
        orderProcess()
        if orderInfo["dealAmount"] == 0:
            trend = trendBak
            OKClient.writeLog("#orderCanceled")
        elif trend == "buy":
            shift += orderDiff
        elif trend == "sell":
            shift = float(config.get("kline", "shift"))
    trendBak = trend
    print('ma%(ma1)s:%(maU)s  ma%(ma2)s:%(maL)s diff:%(diff)s shift:%(shift)s p:%(p)s' % {'ma1': ma1, 'maU': maU,
                                                                                          'ma2': ma2, 'maL': maL,
                                                                                          'diff': round(diff, 2),
                                                                                          'shift': round(shift, 2),
                                                                                          'p': round(diff - shift, 2)})
    sys.stdout.flush()


def currentVsMa():
    global trendBak, orderInfo, shift, ma2, orderDiff, current
    current = OKClient.getCoinPrice(symbol, "buy")
    ma = getMA(ma2)
    diff = current - ma
    # if diff > 2 * shift:
    #     shift += shift / 2
    # elif float(config.get("kline", "shift")) < diff < shift / 2:
    #     shift -= shift / 2
    # elif diff < 0:
    #     shift = float(config.get("kline", "shift"))
    if diff > shift:
        trend = "buy"
    else:
        trend = "sell"
    if trendBak != "" and trendBak != trend:
        # sendEmail("trend changed:" + trendBak + "->" + trend)
        OKClient.setOrderInfo(symbol, trend, getAmount(), transaction)
        if trend == "buy" or trend == "sell" and orderInfo["amount"] >= 0.01:
            if trend == "buy":
                OKClient.orderList = []
                OKClient.writeLog("-----------------------------------------------------------------------")
            orderProcess()
            if orderInfo["dealAmount"] == 0:
                trend = trendBak
                OKClient.writeLog("#orderCanceled")
            elif trend == "buy":
                shift += orderDiff
            elif trend == "sell":
                shift = float(config.get("kline", "shift"))
    trendBak = trend
    print(
        'current:%(current)s  ma%(ma2)s:%(ma)s diff:%(diff)s shift:%(shift)s %(p)s' % {'current': current,
                                                                                       'ma2': ma2, 'ma': ma,
                                                                                       'diff': round(diff, 2),
                                                                                       'shift': round(shift, 2),
                                                                                       'p': round(diff - shift, 2)})
    sys.stdout.flush()
    # adjust ma2
    if symbol == "btc_cny" and ma2 == int(config.get("strategy", "cross").split("|")[1]) and diff < -180:
        ma2 = int(config.get("strategy", "cross").split("|")[1]) + 30
        print("##### diff too heigh , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})
        OKClient.writeLog("##### diff too heigh , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})
    elif symbol == "btc_cny" and ma2 == int(config.get("strategy", "cross").split("|")[1]) + 30 and diff > 100:
        ma2 = int(config.get("strategy", "cross").split("|")[1])
        print("##### diff too heigh , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})
        OKClient.writeLog("##### diff too heigh , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})


def currentVsCurrent():
    global trendBak, orderInfo, orderDiff, currentList, current
    current = OKClient.getCoinPrice(symbol, "buy")
    currentList.insert(0, current)
    if len(currentList) > 10:
        currentList.pop()
    else:
        print("waiting data:%(len)s" % {'len': len(currentList)})
        return
    _avg = round(sum(currentList) / len(currentList), 2)
    _max = max(currentList)
    _min = min(currentList)
    _depth = round(_max - _min, 2)
    dd = _avg - current
    dx = _max - current
    dy = current - _min
    print(
        "current %(current)s  avg %(avg)s  max %(max)s  min %(min)s depth %(depth)s" % {'current': current, 'avg': _avg,
                                                                                        'max': _max, 'min': _min,
                                                                                        'depth': _depth})
    # rcount = len(list(filter(lambda cu: cu > _avg, currentList)))
    trend = trendBak
    if dy == 0:
        trend = "sell"
    elif dd > 0 and dy > _depth * 0.2:
        trend = "buy"
    elif dd < 0 and dx < _depth * 0.2:
        trend = "sell"
    if trendBak != "" and trendBak != trend:
        OKClient.setOrderInfo(symbol, trend, getAmount(), transaction)
        if trend == "buy" or trend == "sell" and orderInfo["amount"] >= 0.01:
            if trend == "buy":
                OKClient.orderList = []
                OKClient.writeLog("-----------------------------------------------------------------------")
            orderProcess()
            if orderInfo["dealAmount"] == 0:
                trend = trendBak
                OKClient.writeLog("#orderCanceled")
    trendBak = trend
    # print(min(currentList))
    # print(max(currentList))


def checkTransCount():
    global ma2, transCountBak, transMode
    config.read("config.ini")
    transCount = int(config.get("trade", "transcount"))
    if transCount - transCountBak >= 2:
        if transMode == "minus":
            ma2 -= 5
            if ma2 <= (int(config.get("strategy", "cross").split("|")[1]) - 15):
                transMode = "plus"
        else:
            ma2 += 5
            if ma2 >= int(config.get("strategy", "cross").split("|")[1]):
                transMode = "minus"
        print("##### trans too many , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})
        OKClient.writeLog("##### trans too many , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})
    transCountBak = transCount
    timer = threading.Timer(60, checkTransCount)
    timer.start()


# checkTransCount()
OKClient.showAccountInfo()
while True:
    strategy = maXVsMaX
    if ma1 == "current":
        if ma2 == "current":
            strategy = currentVsCurrent
        else:
            strategy = currentVsMa
    try:
        strategy()
    except Exception as err:
        print(err)
    time.sleep(0.5)
