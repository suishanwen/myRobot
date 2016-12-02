#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
# 客户端调用，用于查看API返回结果

import time, sys, configparser

from util.MyUtil import fromDict, fromTimeStamp, sendEmail
from api.OkcoinSpotAPI import OKCoinSpot

# 读取比率配置
config = configparser.ConfigParser()
config.read("../key.ini")
config.read("config.ini")

# 初始化apikey，secretkey,url
apikey = config.get("okcoin", "apikey")
secretkey = config.get("okcoin", "secretkey")
okcoinRESTURL = 'www.okcoin.cn'  # 请求注意：国内账号需要 修改为 www.okcoin.cn

# 现货API
okcoinSpot = OKCoinSpot(okcoinRESTURL, apikey, secretkey)

symbol = config.get("kline", "symbol")
type = config.get("kline", "type")
transaction = float(config.get("kline", "transaction"))
tradeWaitCount = int(config.get("kline", "tradeWaitCount"))

orderInfo = {"symbol": symbol, "type": "", "price": 0, "amount": 0, "dealAmount": 0, "transaction": 0}
buyPrice = 0
totalTransaction = 0


def setOrderInfo(type, amount=0):
    global orderInfo
    orderInfo['type'] = type
    orderInfo['amount'] = amount
    orderInfo['price'] = 0
    orderInfo['dealAmount'] = 0
    if amount > 0:
        orderInfo['transaction'] = 0
    else:
        orderInfo['transaction'] = transaction


def setPrice(price):
    global orderInfo
    orderInfo['price'] = price


def setDealAmount(dealAmount):
    global orderInfo
    orderInfo['dealAmount'] = dealAmount


def setTransaction(type):
    if type == "plus":
        orderInfo['transaction'] = round(orderInfo['transaction'] + orderInfo['dealAmount'] * orderInfo['price'], 2)
    else:
        orderInfo['transaction'] = round(orderInfo['transaction'] - orderInfo['dealAmount'] * orderInfo['price'], 2)


def getBuyAmount(price, accuracy=2):
    global orderInfo
    return round(orderInfo['transaction'] / price, accuracy)


def getUnhandledAmount():
    global orderInfo
    return round(float(orderInfo["amount"]) - float(orderInfo["dealAmount"]), 4)


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
    print(u'-----------------------------------------------现货下单----------------------------------------------------')
    result = okcoinSpot.trade(symbol, type, price, amount)
    if result['result']:
        setPrice(price)
        print("OrderId", result['order_id'], symbol, type, price, amount, "  ", fromTimeStamp(int(time.time())))
        return result['order_id']
    else:
        print("下单失败！", symbol, type, price, amount)
        return "-1"


# print (u' 现货批量下单 ')
# print (okcoinSpot.batchTrade('ltc_usd','buy','[{price:0.1,amount:0.2},{price:0.1,amount:0.2}]'))
def cancelOrder(symbol, orderId):
    print(u'---------------------------------------------现货取消订单--------------------------------------------------')
    result = okcoinSpot.cancelOrder(symbol, orderId)
    if result['result']:
        print(u"订单", result['order_id'], "撤销成功")
    else:
        print(u"订单", orderId, "撤销失败！！！")
    return checkOrderStatus("ltc_cny", orderId)


def checkOrderStatus(symbol, orderId, watiCount=0):
    orderResult = okcoinSpot.orderinfo(symbol, orderId)
    if orderResult["result"]:
        orders = orderResult["orders"]
        if len(orders) > 0:
            order = orders[0]
            orderId = order["order_id"]
            status = order["status"]
            setDealAmount(order["deal_amount"])
            if status == -1:
                print("订单", orderId, "已撤销")
            elif status == 0:
                if watiCount == 30:
                    print("超时未成交")
                else:
                    print("未成交", end=" ")
                    sys.stdout.flush()
            elif status == 1:
                global orderInfo
                if watiCount == 30:
                    print("部分成交 ", orderInfo["dealAmount"])
                else:
                    print("部分成交 ", orderInfo["dealAmount"], end=" ")
                    sys.stdout.flush()
            elif status == 2:
                print("订单", orderId, "完全成交")
            elif status == 3:
                print("订单", orderId, "扯单处理中")
            return status
    else:
        print(orderId, "未查询到订单信息")
        return -2


def btcTrade(type, amount):
    global tradeWaitCount
    price = getCoinPrice("btc_cny", type)
    if type == "buy":
        amount = getBuyAmount(price, 4)
    orderId = makeOrder("btc_cny", type, price, amount)
    if orderId != "-1":
        watiCount = 0
        status = 0
        while watiCount < (tradeWaitCount + 1) and status != 2:
            status = checkOrderStatus("btc_cny", orderId, watiCount)
            time.sleep(1)
            watiCount += 1
            if watiCount == tradeWaitCount and status != 2:
                global orderInfo
                if getCoinPrice("btc_cny", type) == orderInfo["price"]:
                    watiCount -= int(tradeWaitCount/3)
        if status != 2:
            status = cancelOrder("btc_cny", orderId)
        return status
    else:
        return -2


def ltcTrade(type, amount):
    price = getCoinPrice("ltc_cny", type)
    if type == "buy":
        amount = getBuyAmount(price)
    orderId = makeOrder("ltc_cny", type, price, amount)
    if orderId != "-1":
        watiCount = 0
        status = 0
        while watiCount < (tradeWaitCount + 1) and status != 2:
            status = checkOrderStatus("ltc_cny", orderId, watiCount)
            time.sleep(1)
            watiCount += 1
            if watiCount == tradeWaitCount and status != 2:
                global orderInfo
                if getCoinPrice("ltc_cny", type) == orderInfo["price"]:
                    watiCount -= int(tradeWaitCount/3)
        if status != 2:
            status = cancelOrder("ltc_cny", orderId)
        return status
    else:
        return -2


def getCoinPrice(symbol, type):
    if symbol == "btc_cny":
        if type == "buy":
            return round(float(okcoinSpot.ticker('btc_cny')["ticker"]["buy"]), 2) + 0.01
        else:
            return round(float(okcoinSpot.ticker('btc_cny')["ticker"]["sell"]), 2) - 0.01
    else:
        if type == "buy":
            return round(float(okcoinSpot.ticker('ltc_cny')["ticker"]["buy"]), 2)
        else:
            return round(float(okcoinSpot.ticker('ltc_cny')["ticker"]["sell"]), 2)


def writeLog(text=""):
    global orderInfo
    f = open(r'log.txt', 'a')
    if text == "":
        f.writelines(' '.join(
            ["\n", orderInfo["symbol"], orderInfo["type"], str(orderInfo["price"]), str(orderInfo["dealAmount"]),
             str(orderInfo["transaction"]), str(fromTimeStamp(int(time.time())))]))
    else:
        f.writelines("\n" + text)
    f.close()


def showAccountInfo():
    print(u'-----------------------------------------用户现货账户信息--------------------------------------------------')
    myAccountInfo = okcoinSpot.userinfo()
    if myAccountInfo["result"]:
        asset = fromDict(myAccountInfo, "info", "funds", "asset")
        freezed = fromDict(myAccountInfo, "info", "funds", "freezed")
        free = fromDict(myAccountInfo, "info", "funds", "free")
        print(u"RMB总金额", asset["total"], "可用", free["cny"], "冻结", freezed["cny"])
        print(u"BTC可用数量", free["btc"], "冻结数量", freezed["btc"])
        print(u"LTC可用数量", free["ltc"], "冻结数量", freezed["ltc"])
    else:
        print("showAccountInfo Fail,Try again!")
        showAccountInfo()


def showCurrentMarket(sleepCount=0):
    btc = okcoinSpot.ticker('btc_cny')
    ltc = okcoinSpot.ticker('ltc_cny')
    btcTicker = btc["ticker"]
    ltcTicker = ltc["ticker"]
    if sleepCount > 0:
        print(u"BTC 买一", btcTicker["buy"], "卖一", btcTicker["sell"], "LTC 买一", ltcTicker["buy"], "卖一", ltcTicker["sell"])
    else:
        print(
            u'----------------------------------------------现货行情-----------------------------------------------------')
        print(u"BTC 买一", btcTicker["buy"], "卖一", btcTicker["sell"], "  24H 高", btcTicker["high"], "低", btcTicker["low"],
              "成交",
              btcTicker["vol"], "        ", fromTimeStamp(btc['date']))
        print(u"LTC 买一", ltcTicker["buy"], "卖一", ltcTicker["sell"], "  24H 高", ltcTicker["high"], "低", ltcTicker["low"],
              "成交",
              ltcTicker["vol"], "        ", fromTimeStamp(ltc['date']))


def btcFun():
    global orderInfo, buyPrice, totalTransaction,transaction
    status = btcTrade(orderInfo["type"], getUnhandledAmount())
    # 非下单失败
    if status != -2:
        setTransaction("minus")
        writeLog()
        if orderInfo["type"] == "buy":
            buyPrice = orderInfo["price"]
            totalTransaction = totalTransaction + orderInfo["transaction"]
        else:
            totalTransaction = totalTransaction - orderInfo["transaction"]
            writeLog(' '.join(
                ["priceDiff:", str(round(orderInfo["price"] - buyPrice, 2)), "transactionDiff:",
                 str(round(totalTransaction - transaction,2)), "totalTransaction:", str(round(totalTransaction,2))]))
            totalTransaction = 0
    if status == 2:
        showAccountInfo()
        showCurrentMarket()
    else:
        btcFun()


def ltcFun():
    global orderInfo, buyPrice, totalTransaction, transaction
    status = ltcTrade(orderInfo["type"], getUnhandledAmount())
    # 非下单失败
    if status != -2:
        setTransaction("minus")
        writeLog()
        if orderInfo["type"] == "buy":
            buyPrice = orderInfo["price"]
            totalTransaction = totalTransaction + orderInfo["ransaction"]
        else:
            totalTransaction = totalTransaction - orderInfo["ransaction"]
            writeLog(' '.join(
                ["priceDiff:", str(round(orderInfo["price"] - buyPrice, 2)), "transactionDiff:",
                 str(round(totalTransaction - transaction, 2)), "totalTransaction:", str(round(totalTransaction, 2))]))
            totalTransaction = 0
    if status == 2:
        showAccountInfo()
        showCurrentMarket()
    else:
        ltcFun()


def getMA(param):
    ms = int(time.time() * 1000)
    if type == "15min":
        ms -= param * 15 * 60 * 1000
    elif type == "1min":
        ms -= param * 1 * 60 * 1000
    data = okcoinSpot.klines(symbol, type, param, ms)
    ma = 0
    if len(data) != param:
        raise Exception("等待数据...")
    for line in data:
        ma += line[4]
    return round(ma / param, 2)


trend = ""
trendBak = ""
showAccountInfo()
while True:
    try:
        ma7 = getMA(7)
        ma30 = getMA(30)
        if ma7 >= ma30:
            trend = "buy"
        else:
            trend = "sell"
        if trendBak != "" and trendBak != trend:
            sendEmail("趋势发生改变:" + trendBak + "->" + trend)
            if symbol == "btc_cny":
                if trend == "buy":
                    setOrderInfo("buy")
                else:
                    setOrderInfo("sell", getCoinNum(symbol))
                btcFun()
            elif symbol == "ltc_cny":
                if trend == "buy":
                    setOrderInfo(trend)
                else:
                    setOrderInfo(trend, getCoinNum(symbol))
                ltcFun()
        trendBak = trend
        print('ma7:%(ma7)s  ma30:%(ma30)s diff:%(diff)s' % {'ma7': ma7, 'ma30': ma30, 'diff': round(ma7 - ma30, 2)})
        sys.stdout.flush()
    except Exception as err:
        print(err)
    time.sleep(1)
