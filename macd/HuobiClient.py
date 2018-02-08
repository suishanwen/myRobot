#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
import sys, importlib

sys.path.append("/home/myRobot")
importlib.reload(sys)

import time, configparser, threading
import common.HuobiProClient as HuobiClient

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
orderInfo = HuobiClient.orderInfo
orderDiff = HuobiClient.orderDiff
tradeRemain = 0


def calAvgReward():
    global tradeRemain
    orderBuyList = list(filter(lambda orderIn: orderIn["type"] == HuobiClient.TRADE_BUY, HuobiClient.orderList))
    orderSellList = list(filter(lambda orderIn: orderIn["type"] == HuobiClient.TRADE_SELL, HuobiClient.orderList))
    buyAmount = 0
    buyCost = 0
    sellAmount = 0
    sellReward = 0
    fee = 0
    for order in orderBuyList:
        buyAmount += float(order["field-amount"])
        buyCost += float(order["field-cash-amount"])
        fee += float(order["field-fees"]) * float(order["field-cash-amount"]) / float(order["field-amount"])
    buyAvg = buyCost / buyAmount
    for order in orderSellList:
        sellAmount += float(order["field-amount"])
        sellReward += float(order["field-cash-amount"])
        fee += float(order["field-fees"])
    tradeRemain = buyAmount - sellAmount
    sellAvg = sellReward / sellAmount
    avgReward = round(sellAvg - buyAvg, 3)
    config.read("config.ini")
    config.set("statis", "avgreward", str(round(float(config.get("statis", "avgreward")) + avgReward, 5)))
    config.set("statis", "reward", str(round(float(config.get("statis", "reward")) + sellReward - buyCost, 5)))
    config.set("statis", "transcount", str(int(config.get("statis", "transcount")) + 1))
    config.set("statis", "fee", str(round(float(config.get("statis", "fee")) + fee, 5)))
    config.set("statis", "realReward",
               str(round(
                   float(config.get("statis", "reward")) + sellReward - buyCost - float(config.get("statis", "fee")),
                   5)))

    fp = open("config.ini", "w")
    config.write(fp)
    HuobiClient.writeLog(' '.join(
        ["avgPriceDiff:", str(avgReward), "fee", str(round(fee, 3)), "transactionReward:",
         str(round(sellReward - buyCost - fee, 5))]))


def getAmount():
    orderBuyList = list(filter(lambda orderIn: orderIn["type"] == HuobiClient.TRADE_BUY, HuobiClient.orderList))
    totalAmount = 0
    for order in orderBuyList:
        totalAmount += float(order["field-amount"])
    if totalAmount != 0:
        totalAmount += tradeRemain
    return totalAmount


def orderProcess():
    global orderInfo, current, symbol
    amount = HuobiClient.getUnhandledAmount()
    state = HuobiClient.trade(symbol, orderInfo["type"], amount, current)
    # dealed or part dealed
    if state != 'partial-canceled' and state != 'canceled':
        HuobiClient.setTransaction("minus")
        HuobiClient.writeLog()
    if state == 'filled':
        if orderInfo["type"] == HuobiClient.TRADE_SELL:
            print(HuobiClient.orderList)
            calAvgReward()
    elif orderInfo["dealAmount"] != 0:
        orderProcess()


def getMA(param):
    result = HuobiClient.get_kline(symbol, type, param)
    if result["status"] == 'ok':
        data = result["data"]
        ma = 0
        for line in data:
            ma += line['close']
        return round(ma / len(data), 4)
    else:
        return getMA(param)


def maXVsMaX():
    global trendBak, shift
    maU = getMA(ma1)
    maL = getMA(ma2)
    diff = maU - maL
    if diff > shift:
        trend = HuobiClient.TRADE_BUY
    else:
        trend = HuobiClient.TRADE_SELL
    if trendBak != "" and trendBak != trend:
        # sendEmail("trend changed:" + str(maU) + " VS " + str(maL))
        HuobiClient.setOrderInfo(symbol, trend, getAmount(), transaction)
        if trend == HuobiClient.TRADE_BUY:
            HuobiClient.orderList = []
            HuobiClient.writeLog("-----------------------------------------------------------------------")
        orderProcess()
        if orderInfo["dealAmount"] == 0:
            trend = trendBak
            HuobiClient.writeLog("#orderCanceled")
        elif trend == HuobiClient.TRADE_BUY:
            shift += orderDiff
        elif trend == HuobiClient.TRADE_SELL:
            shift = float(config.get("kline", "shift"))
    trendBak = trend
    print('ma%(ma1)s:%(maU)s  ma%(ma2)s:%(maL)s diff:%(diff)s shift:%(shift)s p:%(p)s' % {'ma1': ma1, 'maU': maU,
                                                                                          'ma2': ma2, 'maL': maL,
                                                                                          'diff': round(diff, 4),
                                                                                          'shift': round(shift, 4),
                                                                                          'p': round(diff - shift, 4)})
    sys.stdout.flush()


def currentVsMa():
    global trendBak, orderInfo, shift, ma2, orderDiff, current
    current = HuobiClient.getCoinPrice(HuobiClient.SYMBOL_HT)
    ma = getMA(ma2)
    diff = current - ma
    # if diff > 2 * shift:
    #     shift += shift / 2
    # elif float(config.get("kline", "shift")) < diff < shift / 2:
    #     shift -= shift / 2
    # elif diff < 0:
    #     shift = float(config.get("kline", "shift"))
    if diff > shift:
        trend = HuobiClient.TRADE_BUY
    else:
        trend = HuobiClient.TRADE_SELL
    if trendBak != "" and trendBak != trend:
        # sendEmail("trend changed:" + trendBak + "->" + trend)
        HuobiClient.setOrderInfo(symbol, trend, getAmount(), transaction)
        if trend == HuobiClient.TRADE_BUY or trend == HuobiClient.TRADE_SELL and orderInfo["amount"] >= 0.01:
            if trend == HuobiClient.TRADE_BUY:
                HuobiClient.orderList = []
                HuobiClient.writeLog("-----------------------------------------------------------------------")
            orderProcess()
            if orderInfo["dealAmount"] == 0:
                trend = trendBak
                HuobiClient.writeLog("#orderCanceled")
            elif trend == HuobiClient.TRADE_BUY:
                shift += orderDiff
            elif trend == HuobiClient.TRADE_SELL:
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
        HuobiClient.writeLog("##### diff too heigh , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})
    elif symbol == "btc_cny" and ma2 == int(config.get("strategy", "cross").split("|")[1]) + 30 and diff > 100:
        ma2 = int(config.get("strategy", "cross").split("|")[1])
        print("##### diff too heigh , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})
        HuobiClient.writeLog("##### diff too heigh , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})


def currentVsCurrent():
    global trendBak, orderInfo, orderDiff, currentList, current
    current = HuobiClient.getTradePrice(symbol, HuobiClient.TRADE_BUY)
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
        trend = HuobiClient.TRADE_SELL
    elif dd > 0 and dy > _depth * 0.2:
        trend = HuobiClient.TRADE_BUY
    elif dd < 0 and dx < _depth * 0.2:
        trend = HuobiClient.TRADE_SELL
    if trendBak != "" and trendBak != trend:
        HuobiClient.setOrderInfo(symbol, trend, getAmount(), transaction)
        if trend == HuobiClient.TRADE_BUY or trend == HuobiClient.TRADE_SELL and orderInfo["amount"] >= 0.01:
            if trend == HuobiClient.TRADE_BUY:
                HuobiClient.orderList = []
                HuobiClient.writeLog("-----------------------------------------------------------------------")
            orderProcess()
            if orderInfo["dealAmount"] == 0:
                trend = trendBak
                HuobiClient.writeLog("#orderCanceled")
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
        HuobiClient.writeLog("##### trans too many , adjust ma2 to %(ma2)s #####" % {'ma2': ma2})
    transCountBak = transCount
    timer = threading.Timer(60, checkTransCount)
    timer.start()


# checkTransCount()
trendBak = HuobiClient.TRADE_SELL
HuobiClient.getAccountInfo([HuobiClient.BALANCE_HT, HuobiClient.BALANCE_USDT])
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
    time.sleep(0.1)
