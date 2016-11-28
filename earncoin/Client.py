#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
# 客户端调用，用于查看API返回结果

import configparser
import sys
import time

from MyUtil import fromDict, fromTimeStamp,sendEmail

from earncoin.OkcoinSpotAPI import OKCoinSpot

# 初始化apikey，secretkey,url
apikey = '*******************************************'
secretkey = '*******************************************'
okcoinRESTURL = 'www.okcoin.cn'  # 请求注意：国内账号需要 修改为 www.okcoin.cn

# 现货API
okcoinSpot = OKCoinSpot(okcoinRESTURL, apikey, secretkey)

# 读取比率配置
config = configparser.ConfigParser()
config.read("config.ini")

global baseRate, orderInfo, btcPerAmount,shiftRate,lastRecordTime,switch
baseRate = round(float(config.get("base", "baseRate")), 5)
shiftRate = round(float(config.get("shift", "shiftRate")), 6)
orderInfo = {"symbol": "", "type": "", "price": 0, "amount": 0, "dealAmount": 0, "transaction": 0}
btcPerAmount = 0.01
lastRecordTime=0
switch={"email":False}
def setOrderInfo(symbol, type, amount=0):
    global orderInfo
    orderInfo['symbol'] = symbol
    orderInfo['type'] = type
    orderInfo['amount'] = amount
    orderInfo['price'] = 0
    orderInfo['dealAmount'] = 0
    if amount > 0:
        orderInfo['transaction'] = 0


def setPrice(price):
    global orderInfo
    orderInfo['price'] = price


def setDealAmount(dealAmount):
    global orderInfo
    orderInfo['dealAmount'] = dealAmount


def setTransaction(type):
    if type == "plus":
        orderInfo['transaction'] = round(orderInfo['transaction'] + orderInfo['dealAmount'] * orderInfo['price'],2)
    else:
        orderInfo['transaction'] = round(orderInfo['transaction'] - orderInfo['dealAmount'] * orderInfo['price'],2)


def getBuyAmount(price,accuracy=2):
    global orderInfo
    return round(orderInfo['transaction'] / price, accuracy)


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


def getUnhandledAmount():
    global orderInfo
    return round(float(orderInfo["amount"]) - float(orderInfo["dealAmount"]), 2)


def resetBaseRate(shift):
    global baseRate
    baseRate += shift
    config.set("base", "baseRate", str(round(baseRate, 5)))
    config.write(open("config.ini", "w"))
    baseRate = round(float(config.get("base", "baseRate")), 5)

def delaySendEmail(secondTime,price):
    global lastRecordTime
    if secondTime-lastRecordTime>30:
        lastRecordTime=secondTime
        print("sendEmail ---> Warning : LTC current price is "+price)
        sendEmail("Warning : LTC current price is "+price)

def watchBuyInfo():
    global baseRate, btcPerAmount,shiftRate
    btc = okcoinSpot.ticker('btc_cny')
    ltc = okcoinSpot.ticker('ltc_cny')
    btcTicker = btc["ticker"]
    ltcTicker = ltc["ticker"]
    if float(ltcTicker["buy"])<31.59 and switch["email"]:
        delaySendEmail(int(ltc["date"]),ltcTicker["buy"])

    rate = round(float(ltcTicker["buy"]) / float(btcTicker["buy"]), 6)
    if rate <= baseRate - shiftRate:
        num = getCoinNum("btc_cny")
        if num >= btcPerAmount:
            print(
                u'----------------------------------------------阀值触发-----------------------------------------------------')
            print(u"BTC", btcTicker["buy"], "LTC", ltcTicker["buy"], "比", rate, "    ", fromTimeStamp(btc["date"]))
            print("进入btcToLtc流程...")
            writeLog(u"\nEnter btcToLtc process... baseRate:" + str(baseRate) + " rate:" + str(rate))
            setOrderInfo("btc_cny", "sell", btcPerAmount)
            btcToLtc()
    elif rate >= baseRate + shiftRate:
        num = getCoinNum("ltc_cny")
        if num >= btcPerAmount / baseRate:
            print(
                u'----------------------------------------------阀值触发-----------------------------------------------------')
            print(u"BTC", btcTicker["buy"], "LTC", ltcTicker["buy"], "比", rate, "    ", fromTimeStamp(btc["date"]))
            print("进入ltcToBtc流程...")
            writeLog(u"\nEnter ltcToBtc process... baseRate:" + str(baseRate) + " rate:" + str(rate))
            setOrderInfo("ltc_cny", "sell", round(btcPerAmount / (baseRate + shiftRate), 2))
            ltcToBtc()


def btcToLtc():
    global baseRate, btcPerAmount
    status = btcTrade("sell", getUnhandledAmount())
    setTransaction("plus")
    writeLog()
    if status == 2:
        setOrderInfo("ltc_cny", "buy")
        ltcFun()
    elif status == 1:
        btcToLtc()


def ltcFun():
    status = ltcTrade("buy", getUnhandledAmount())
    # 非下单失败
    if status != -2:
        setTransaction("minus")
        writeLog()
    if status == 2:
        global shiftRate,baseRate
        resetBaseRate(-shiftRate)
        print("btcToLtc 转换成功！")
        sendEmail("btcToLtc 转换成功！当前比率" + str(baseRate))
        showAccountInfo()
        showCurrentMarket()
    else:
        ltcFun()


def ltcToBtc():
    global baseRate, btcPerAmount
    status = ltcTrade("sell", getUnhandledAmount())
    setTransaction("plus")
    writeLog()
    if status == 2:
        setOrderInfo("btc_cny", "buy")
        btcFun()
    elif status == 1:
        btcToLtc()


def btcFun():
    status = btcTrade("buy", getUnhandledAmount())
    # 非下单失败
    if status != -2:
        setTransaction("minus")
        writeLog()
    if status == 2:
        global shiftRate,baseRate
        resetBaseRate(shiftRate)
        print("ltcToBtc 转换成功！")
        sendEmail("ltcToBtc 转换成功！当前比率" + str(baseRate))
        showAccountInfo()
        showCurrentMarket()
    else:
        btcFun()


def btcTrade(type, amount):
    price = getCoinPrice("btc_cny", type)
    if type == "buy":
        amount = getBuyAmount(price,3)
    orderId = makeOrder("btc_cny", type, price, amount)
    if orderId != "-1":
        watiCount = 0
        status = 0
        while watiCount < 31 and status != 2:
            status = checkOrderStatus("btc_cny", orderId, watiCount)
            time.sleep(1)
            watiCount += 1
            if watiCount == 30 and status != 2:
                global orderInfo
                if getCoinPrice("btc_cny", type) == orderInfo["price"]:
                    watiCount -= 10
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
        while watiCount < 31 and status != 2:
            status = checkOrderStatus("ltc_cny", orderId, watiCount)
            time.sleep(1)
            watiCount += 1
            if watiCount == 30 and status != 2:
                global orderInfo
                if getCoinPrice("ltc_cny", type) == orderInfo["price"]:
                    watiCount -= 10
        if status != 2:
            status=cancelOrder("ltc_cny", orderId)
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


def showCurrentMarket(sleepCount=0):
    global baseRate
    btc = okcoinSpot.ticker('btc_cny')
    ltc = okcoinSpot.ticker('ltc_cny')
    btcTicker = btc["ticker"]
    ltcTicker = ltc["ticker"]
    if sleepCount > 0:
        print(u"BTC 买一", btcTicker["buy"], "卖一", btcTicker["sell"], "LTC 买一", ltcTicker["buy"], "卖一", ltcTicker["sell"],
              "偏移", int((float(ltcTicker["buy"]) / float(btcTicker["buy"]) - baseRate) * 1000000))
    else:
        print(
            u'----------------------------------------------现货行情-----------------------------------------------------')
        print(u"BTC 买一", btcTicker["buy"], "卖一", btcTicker["sell"], "  24H 高", btcTicker["high"], "低", btcTicker["low"],
              "成交",
              btcTicker["vol"], "        ", fromTimeStamp(btc['date']))
        print(u"LTC 买一", ltcTicker["buy"], "卖一", ltcTicker["sell"], "  24H 高", ltcTicker["high"], "低", ltcTicker["low"],
              "成交",
              ltcTicker["vol"], "        ", fromTimeStamp(ltc['date']))
        print(u"比率", round(float(ltcTicker["buy"]) / float(btcTicker["buy"]), 6), "基准比率", baseRate)


# print (u' 现货深度 ')
# print (okcoinSpot.depth('btc_cny'))
# def showOdersHistory():
#     print(u'-----------------------------------------------------------------------------------------------------')
#     print (u' 现货历史交易信息 ')
#     orders=okcoinSpot.trades()
#     for order in orders:
#         print(order)
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


def showOrderInfo():
    print(u'-----------------------------------------现货订单信息查询--------------------------------------------------')
    print(u'                                ----------------BTC-------------------')
    btcOrderResult = okcoinSpot.orderinfo('btc_cny', '-1')
    if btcOrderResult["result"]:
        btcOrders = btcOrderResult['orders']
        for btcOrder in btcOrders:
            print("Id", btcOrder["order_id"], "价格", btcOrder['price'], "数量", btcOrder['amount'], "成功",
                  btcOrder['deal_amount'], "平均", btcOrder['avg_price'], "时间",
                  fromTimeStamp(btcOrder["create_date"] / 1000))
    else:
        print("BTC订单信息获取失败！")

    print(u'                                ----------------LTC-------------------')
    ltcOrderResult = okcoinSpot.orderinfo('ltc_cny', '-1')
    if ltcOrderResult["result"]:
        ltcOrders = ltcOrderResult['orders']
        for ltcOrder in ltcOrders:
            print("Id", ltcOrder["order_id"], "价格", ltcOrder['price'], "数量", ltcOrder['amount'], "成功",
                  ltcOrder['deal_amount'], "平均", ltcOrder['avg_price'], "时间",
                  fromTimeStamp(ltcOrder["create_date"] / 1000))
    else:
        print("LTC订单信息获取失败！")



# print (u' 现货批量订单信息查询 ')
# print (okcoinSpot.ordersinfo('ltc_usd','18243800,18243801,18243644','0'))

# print (u' 现货历史订单信息查询 ')
# print (okcoinSpot.orderHistory('ltc_usd','0','1','2'))


# orderId=makeOrder("ltc_cny","sell","30","0.1")
# if orderId!="-1":
#     cancelOrder("ltc_cny", orderId)



showAccountInfo()
showOrderInfo()
showCurrentMarket()

print(u'--------------------------------------------现货行情监控---------------------------------------------------')
sleepCount = 0
while True:
    if sleepCount == 60:
        showCurrentMarket()
        sleepCount = 0
    elif sleepCount % 5 == 0:
        showCurrentMarket(1)
    time.sleep(0.5)
    sleepCount += 1
    watchBuyInfo()
