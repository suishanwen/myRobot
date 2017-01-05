#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8

import time, sys, configparser, importlib

sys.path.append("/home/python")
importlib.reload(sys)
from util.MyUtil import fromDict, fromTimeStamp, sendEmail
from api.OkcoinSpotAPI import OKCoinSpot

# read config
config = configparser.ConfigParser()
config.read("../key.ini")
config.read("config.ini")

# init apikey，secretkey,url
apikey = config.get("okcoin", "apikey")
secretkey = config.get("okcoin", "secretkey")
okcoinRESTURL = 'www.okcoin.cn'

# currentAPI
okcoinSpot = OKCoinSpot(okcoinRESTURL, apikey, secretkey)

# getConfig
symbol = config.get("kline", "symbol")
type = config.get("kline", "type")
cross = config.get("kline", "cross")
ma1 = cross.split("|")[0]
if ma1 != "current":
    ma1 = int(ma1)
ma2 = int(cross.split("|")[1])
shift = float(config.get("kline", "shift"))
transaction = float(config.get("trade", "transaction"))
tradeWaitCount = int(config.get("trade", "tradeWaitCount"))
orderDiff = float(config.get("trade", "orderDiff"))

# global variable
orderInfo = {"symbol": symbol, "type": "", "price": 0, "amount": 0, "avgPrice": 0, "dealAmount": 0, "transaction": 0}
orderList = []
trendBak = ""


def setOrderInfo(type):
    global orderInfo, symbol
    orderInfo['type'] = type
    if type == "sell":
        orderInfo['amount'] = getCoinNum(symbol)
    else:
        orderInfo['amount'] = 0
    orderInfo['price'] = 0
    orderInfo['dealAmount'] = 0
    if orderInfo['amount'] > 0:
        orderInfo['transaction'] = 0
    else:
        orderInfo['transaction'] = transaction


def setPrice(price):
    global orderInfo
    orderInfo['price'] = price


def setAvgPrice(avgPrice):
    global orderInfo
    orderInfo['avgPrice'] = avgPrice


def setDealAmount(dealAmount):
    global orderInfo
    orderInfo['dealAmount'] = dealAmount


def setTransaction(type):
    global orderInfo
    print(orderInfo)
    if type == "plus":
        orderInfo['transaction'] = round(orderInfo['transaction'] + orderInfo['dealAmount'] * orderInfo['avgPrice'], 2)
    else:
        orderInfo['transaction'] = round(orderInfo['transaction'] - orderInfo['dealAmount'] * orderInfo['avgPrice'], 2)


def getBuyAmount(price, accuracy=2):
    global orderInfo
    return round(orderInfo['transaction'] / price, accuracy)


def getUnhandledAmount():
    global orderInfo
    return round(float(orderInfo["amount"]) - float(orderInfo["dealAmount"]), 5)


def getCoinNum(symbol):
    myAccountInfo = okcoinSpot.userinfo()
    if myAccountInfo["result"]:
        free = fromDict(myAccountInfo, "info", "funds", "free")
        if symbol == "btc_cny":
            return float(free["btc"])
        else:
            return float(free["ltc"])
    else:
        print("getCoinNum Fail,Try again!")
        getCoinNum(symbol)


def makeOrder(symbol, type, price, amount):
    print(
        u'\n---------------------------------------------spot order--------------------------------------------------')
    result = okcoinSpot.trade(symbol, type, price, amount)
    if result['result']:
        setPrice(price)
        print("OrderId", result['order_id'], symbol, type, price, amount, "  ", fromTimeStamp(int(time.time())))
        return result['order_id']
    else:
        print("order failed！", symbol, type, price, amount)
        global orderInfo
        print(orderInfo)
        return "-1"


def cancelOrder(symbol, orderId):
    print(u'\n-----------------------------------------spot cancel order----------------------------------------------')
    result = okcoinSpot.cancelOrder(symbol, orderId)
    if result['result']:
        print(u"order", result['order_id'], "canceled")
    else:
        print(u"order", orderId, "cancel failed！！！")
    status = checkOrderStatus(symbol, orderId)
    if status != -1 and status != 2:  # not canceled or cancel failed(part dealed) continue cancel
        cancelOrder(symbol, orderId)
    return status


def addOrderList(order):
    global orderList
    orderList = list(filter(lambda orderIn: orderIn["order_id"] != order["order_id"], orderList))
    if order["status"] == 1 or order["status"] == 2:
        orderList.append(order)


def checkOrderStatus(symbol, orderId, watiCount=0):
    orderResult = okcoinSpot.orderinfo(symbol, orderId)
    if orderResult["result"]:
        orders = orderResult["orders"]
        if len(orders) > 0:
            order = orders[0]
            orderId = order["order_id"]
            status = order["status"]
            setDealAmount(order["deal_amount"])
            setAvgPrice(order["avg_price"])
            addOrderList(order)
            if status == -1:
                print("order", orderId, "canceled")
            elif status == 0:
                if watiCount == 30:
                    print("timeout no deal")
                else:
                    print("no deal", end=" ")
                    sys.stdout.flush()
            elif status == 1:
                global orderInfo
                if watiCount == 30:
                    print("part dealed ", orderInfo["dealAmount"])
                else:
                    print("part dealed ", orderInfo["dealAmount"], end=" ")
                    sys.stdout.flush()
            elif status == 2:
                print("order", orderId, "complete deal")
            elif status == 3:
                print("order", orderId, "canceling")
            return status
    else:
        print(orderId, " order not found")
        return -2


def trade(type, amount):
    global tradeWaitCount, symbol, orderInfo
    price = getCoinPrice(symbol, type)
    if type == "buy":
        amount = getBuyAmount(price, 4)
    if amount < 0.01:
        return 2
    orderId = makeOrder(symbol, type, price, amount)
    if orderId != "-1":
        watiCount = 0
        status = 0
        global orderInfo
        dealAmountBak = orderInfo["dealAmount"]
        while watiCount < (tradeWaitCount + 1) and status != 2:
            status = checkOrderStatus(symbol, orderId, watiCount)
            time.sleep(1)
            watiCount += 1
            if watiCount == tradeWaitCount and status != 2:
                if getCoinPrice(symbol, type) == orderInfo["price"]:
                    watiCount -= int(tradeWaitCount / 3)
        if status != 2:
            status = cancelOrder(symbol, orderId)
            setDealAmount(dealAmountBak + orderInfo["dealAmount"])
        return status
    else:
        return -2


def getCoinPrice(symbol, type):
    if symbol == "btc_cny":
        if type == "buy":
            return round(float(okcoinSpot.ticker('btc_cny')["ticker"]["buy"]) + orderDiff, 2)
        else:
            return round(float(okcoinSpot.ticker('btc_cny')["ticker"]["sell"]) - orderDiff, 2)
    else:
        if type == "buy":
            return round(float(okcoinSpot.ticker('ltc_cny')["ticker"]["buy"]) + orderDiff, 2)
        else:
            return round(float(okcoinSpot.ticker('ltc_cny')["ticker"]["sell"]) - orderDiff, 2)


def writeLog(text=""):
    global orderInfo
    f = open(r'log.txt', 'a')
    if text == "":
        f.writelines(' '.join(
            ["\n", orderInfo["symbol"], orderInfo["type"], str(orderInfo["price"]), str(orderInfo["avgPrice"]),
             str(orderInfo["dealAmount"]),
             str(round(orderInfo["avgPrice"] * orderInfo["dealAmount"], 2)), str(fromTimeStamp(int(time.time())))]))
    else:
        f.writelines("\n" + text)
    f.close()


def showAccountInfo():
    print(u'---------------------------------------spot account info------------------------------------------------')
    myAccountInfo = okcoinSpot.userinfo()
    if myAccountInfo["result"]:
        asset = fromDict(myAccountInfo, "info", "funds", "asset")
        freezed = fromDict(myAccountInfo, "info", "funds", "freezed")
        free = fromDict(myAccountInfo, "info", "funds", "free")
        print(u"RMB", asset["total"], "available", free["cny"], "freezed", freezed["cny"])
        print(u"BTC", free["btc"], "freezed", freezed["btc"])
        print(u"LTC", free["ltc"], "freezed", freezed["ltc"])
    else:
        print("showAccountInfo Fail,Try again!")
        showAccountInfo()


def calAvgReward(orderList):
    orderBuyList = list(filter(lambda orderIn: orderIn["type"] == 'buy', orderList))
    orderSellList = list(filter(lambda orderIn: orderIn["type"] == 'sell', orderList))
    buyAmount = 0
    buyCost = 0
    for order in orderBuyList:
        buyAmount += order["deal_amount"]
        buyCost += order["deal_amount"] * order["avg_price"]
    buyAvg = buyCost / buyAmount
    sellAmount = 0
    sellReward = 0
    for order in orderSellList:
        sellAmount += order["deal_amount"]
        sellReward += order["deal_amount"] * order["avg_price"]
    sellAvg = sellReward / sellAmount
    avgReward = round(sellAvg - buyAvg, 2)
    config.read("config.ini")
    totalReward = round(float(config.get("trade", "avgreward")) + avgReward, 2)
    config.set("trade", "avgreward", str(totalReward))
    fp = open("config.ini", "w")
    config.write(fp)
    writeLog(' '.join(
        ["avgPriceDiff:", str(avgReward), "transactionReward:",
         str(round(sellReward - buyCost, 2))]))


def orderProcess():
    global orderInfo
    amount = getUnhandledAmount()
    status = trade(orderInfo["type"], amount)
    # dealed or part dealed
    if status != -2:
        setTransaction("minus")
        writeLog()
    if status == 2:
        if orderInfo["type"] == "sell":
            print(orderList)
            calAvgReward(orderList)
        showAccountInfo()
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
    data = okcoinSpot.klines(symbol, type, param, ms)
    ma = 0
    if len(data) != param:
        raise Exception("waiting data...")
    for line in data:
        ma += line[4]
    return round(ma / param, 2)


def maXVsMaX():
    global trendBak, shift, orderList
    maU = getMA(ma1)
    maL = getMA(ma2)
    diff = maU - maL
    if diff > shift:
        trend = "buy"
    else:
        trend = "sell"
    if trendBak != "" and trendBak != trend:
        # sendEmail("trend changed:" + str(maU) + " VS " + str(maL))
        setOrderInfo(trend)
        if trend == "buy":
            orderList = []
            writeLog("-----------------------------------------------------------------------")
        orderProcess()
        if orderInfo["dealAmount"] == 0:
            trend = trendBak
            writeLog("#orderCanceled")
        elif trend == "buy":
            shift = float(config.get("kline", "shift")) / 2
        elif trend == "sell":
            shift = float(config.get("kline", "shift"))
    trendBak = trend
    print('ma%(ma1)s:%(maU)s  ma%(ma2)s:%(maL)s diff:%(diff)s' % {'ma1': ma1, 'maU': maU, 'ma2': ma2, 'maL': maL,
                                                                  'diff': round(diff, 2)})
    sys.stdout.flush()


def currentVsMa():
    global trendBak, orderInfo, shift, orderList,ma2
    current = round(getCoinPrice(symbol, "buy") - orderDiff, 2)
    ma = getMA(ma2)
    diff = current - ma
    if diff > shift:
        trend = "buy"
    else:
        trend = "sell"
    if trendBak != "" and trendBak != trend:
        # sendEmail("trend changed:" + trendBak + "->" + trend)
        setOrderInfo(trend)
        if trend == "buy" or trend == "sell" and orderInfo["amount"] >= 0.01:
            if trend == "buy":
                orderList = []
                writeLog("-----------------------------------------------------------------------")
            orderProcess()
            if orderInfo["dealAmount"] == 0:
                trend = trendBak
                writeLog("#orderCanceled")
            elif trend == "buy":
                shift = float(config.get("kline", "shift")) / 2
            elif trend == "sell":
                shift = float(config.get("kline", "shift"))
    trendBak = trend
    print(
        'current:%(current)s  ma%(ma2)s:%(ma)s diff:%(diff)s' % {'current': current,
                                                                 'ma2': ma2, 'ma': ma,
                                                                 'diff': round(diff, 2)})
    sys.stdout.flush()
    # adjust ma2
    if symbol == "btc_cny" and ma2 == 30 and diff < -150:
        ma2 = 15
        print("##### diff too heigh adjust ma2 to 15 #####")
        writeLog("##### diff too heigh adjust ma2 to 15 #####")
    elif symbol == "btc_cny" and ma2 == 15 and diff > 75:
        ma2 = 30
        print("##### diff too heigh adjust ma2 to 30 #####")
        writeLog("##### diff too heigh adjust ma2 to 30 #####")



showAccountInfo()
while True:
    strategy = maXVsMaX
    if ma1 == "current":
        strategy = currentVsMa
    try:
        strategy()
    except Exception as err:
        print(err)
    time.sleep(1)
