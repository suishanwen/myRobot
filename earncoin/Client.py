#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
# 客户端调用，用于查看API返回结果

import configparser
import time

from util.MyUtil import fromDict, fromTimeStamp, sendEmail
import common.OKClient as OKClient

# 读取比率配置
config = configparser.ConfigParser()
config.read("config.ini")

baseRate = round(float(config.get("base", "baseRate")), 5)
shiftRate = round(float(config.get("shift", "shiftRate")), 6)
btcPerAmount = 0.01
orderInfo = OKClient.orderInfo
orderdiff = OKClient.orderDiff

def resetBaseRate(shift):
    global baseRate
    baseRate += shift
    config.set("base", "baseRate", str(round(baseRate, 5)))
    config.write(open("config.ini", "w"))
    baseRate = round(float(config.get("base", "baseRate")), 5)


def watchBuyInfo():
    global baseRate, btcPerAmount, shiftRate
    btc = OKClient.okcoinSpot.ticker('btc_cny')
    ltc = OKClient.okcoinSpot.ticker('ltc_cny')
    btcTicker = btc["ticker"]
    ltcTicker = ltc["ticker"]
    rate = round(float(ltcTicker["buy"]) / float(btcTicker["buy"]),6)
    if rate <= baseRate - shiftRate:
        num = getCoinNum("btc_cny")
        if num >= btcPerAmount:
            print(
                u'----------------------------------------------阀值触发-----------------------------------------------------')
            print(u"BTC", btcTicker["buy"], "LTC", ltcTicker["buy"], "比", rate, "    ", fromTimeStamp(btc["date"]))
            print("进入btcToLtc流程...")
            OKClient.writeLog(u"\nEnter btcToLtc process... baseRate:" + str(baseRate) + " rate:" + str(rate))
            OKClient.setOrderInfo("btc_cny", "sell", btcPerAmount)
            btcToLtc(float(btcTicker["buy"]) - orderdiff)
    elif rate >= baseRate + shiftRate:
        num = getCoinNum("ltc_cny")
        if num >= btcPerAmount / baseRate:
            print(
                u'----------------------------------------------阀值触发-----------------------------------------------------')
            print(u"BTC", btcTicker["buy"], "LTC", ltcTicker["buy"], "比", rate, "    ", fromTimeStamp(btc["date"]))
            print("进入ltcToBtc流程...")
            OKClient.writeLog(u"\nEnter ltcToBtc process... baseRate:" + str(baseRate) + " rate:" + str(rate))
            OKClient.setOrderInfo("ltc_cny", "sell", round(btcPerAmount / (baseRate + shiftRate), 2))
            ltcToBtc(float(ltcTicker["buy"]) + orderdiff)


def btcToLtc(price=0):
    global baseRate, btcPerAmount
    status = OKClient.trade("btc_cny", "sell", OKClient.getUnhandledAmount(), price)
    OKClient.setTransaction("plus")
    OKClient.writeLog()
    if status == 2:
        OKClient.setOrderInfo("ltc_cny", "buy")
        ltcFun()
    elif status == 1:
        btcToLtc()


def ltcFun():
    status = OKClient.trade("ltc_cny", "buy", OKClient.getUnhandledAmount())
    # 非下单失败
    if status != -2:
        OKClient.setTransaction("minus")
        OKClient.writeLog()
    if status == 2:
        global shiftRate, baseRate
        resetBaseRate(-shiftRate)
        print("btcToLtc 转换成功！")
        sendEmail("btcToLtc 转换成功！当前比率" + str(baseRate))
        showAccountInfo()
        showCurrentMarket()
    else:
        ltcFun()


def ltcToBtc(price=0):
    global baseRate, btcPerAmount
    status = OKClient.trade("ltc_cny", "sell", OKClient.getUnhandledAmount(), price)
    OKClient.setTransaction("plus")
    OKClient.writeLog()
    if status == 2:
        OKClient.setOrderInfo("btc_cny", "buy")
        btcFun()
    elif status == 1:
        btcToLtc()


def btcFun():
    status = OKClient.trade("btc_cny", "buy", OKClient.getUnhandledAmount())
    # 非下单失败
    if status != -2:
        OKClient.setTransaction("minus")
        OKClient.writeLog()
    if status == 2:
        global shiftRate, baseRate
        resetBaseRate(shiftRate)
        print("ltcToBtc 转换成功！")
        sendEmail("ltcToBtc 转换成功！当前比率" + str(baseRate))
        showAccountInfo()
        showCurrentMarket()
    else:
        btcFun()


def showCurrentMarket(sleepCount=0):
    global baseRate
    btc = OKClient.okcoinSpot.ticker('btc_cny')
    ltc = OKClient.okcoinSpot.ticker('ltc_cny')
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

def getCoinNum(symbol):
    myAccountInfo = OKClient.okcoinSpot.userinfo()
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
    myAccountInfo = OKClient.okcoinSpot.userinfo()
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


def showOrderInfo():
    print(u'-----------------------------------------现货订单信息查询--------------------------------------------------')
    print(u'                                ----------------BTC-------------------')
    btcOrderResult = OKClient.okcoinSpot.orderinfo('btc_cny', '-1')
    if btcOrderResult["result"]:
        btcOrders = btcOrderResult['orders']
        for btcOrder in btcOrders:
            print("Id", btcOrder["order_id"], "价格", btcOrder['price'], "数量", btcOrder['amount'], "成功",
                  btcOrder['deal_amount'], "平均", btcOrder['avg_price'], "时间",
                  fromTimeStamp(btcOrder["create_date"] / 1000))
    else:
        print("BTC订单信息获取失败！")

    print(u'                                ----------------LTC-------------------')
    ltcOrderResult = OKClient.okcoinSpot.orderinfo('ltc_cny', '-1')
    if ltcOrderResult["result"]:
        ltcOrders = ltcOrderResult['orders']
        for ltcOrder in ltcOrders:
            print("Id", ltcOrder["order_id"], "价格", ltcOrder['price'], "数量", ltcOrder['amount'], "成功",
                  ltcOrder['deal_amount'], "平均", ltcOrder['avg_price'], "时间",
                  fromTimeStamp(ltcOrder["create_date"] / 1000))
    else:
        print("LTC订单信息获取失败！")


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
