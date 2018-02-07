# -*- coding: utf-8 -*-
# encoding: utf-8

import time, sys
from util.MyUtil import fromDict, fromTimeStamp
from api.HuobiProAPI import *

BALANCE_HT = "ht"
BALANCE_USDT = "usdt"

SYMBOL_HT = "htusdt"

TRADE_BUY = "buy-limit"
TRADE_SELL = "sell-limit"

# read config
config = configparser.ConfigParser()
config.read("config.ini")

# getConfig
tradeWaitCount = int(config.get("trade", "tradeWaitCount"))
orderDiff = float(config.get("trade", "orderDiff"))

# global variable
accountInfo = {BALANCE_USDT: {"total": 0, "available": 0, "freezed": 0},
               BALANCE_HT: {"total": 0, "available": 0, "freezed": 0}}
priceInfo = {SYMBOL_HT: {"ask": 0, "bid": 0}}
orderInfo = {"symbol": "", "type": "", "price": 0, "amount": 0, "avgPrice": 0, "dealAmount": 0, "transaction": 0}
orderList = []


def setOrderInfo(symbol, type, amount=0, transaction=0):
    global orderInfo
    orderInfo['symbol'] = symbol
    orderInfo['type'] = type
    orderInfo['amount'] = amount
    orderInfo['price'] = 0
    orderInfo['dealAmount'] = 0
    if amount > 0:
        orderInfo['transaction'] = 0
    elif transaction != 0:
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
    return fromDict(accountInfo, symbol, "available")


def makeOrder(symbol, type, price, amount):
    print(
        u'\n---------------------------------------------spot order--------------------------------------------------')
    result = send_order(amount, symbol, type, price)
    if result['status'] == 'ok':
        setPrice(price)
        print("OrderId", result['data'], symbol, type, price, amount, "  ", fromTimeStamp(int(time.time())))
        return result['data']
    else:
        print("order failed！", symbol, type, price, amount)
        return "-1"


def cancelOrder(orderId):
    print(u'\n-----------------------------------------spot cancel order----------------------------------------------')
    result = cancel_order(orderId)
    if result['status'] == 'ok':
        print(u"order", result['data'], "canceled")
    else:
        print(u"order", orderId, "not canceled or cancel failed！！！")
    state = checkOrderStatus(orderId)
    if state != 'canceled' and state != 'partial-canceled':  # not canceled or cancel failed(part dealed) continue cancel
        cancelOrder(orderId)
    return state


def addOrderList(order):
    global orderList
    orderList = list(filter(lambda orderIn: orderIn["id"] != order["id"], orderList))
    if float(order["field-amount"]) > 0:
        orderList.append(order)


def checkOrderStatus(orderId, watiCount=0):
    orderResult = order_info(orderId)
    if orderResult["status"] == 'ok':
        order = orderResult["data"]
        orderId = order["id"]
        state = order["state"]
        setDealAmount(float(order["field-amount"]))
        if orderInfo['dealAmount'] > 0:
            setAvgPrice(float(order["field-cash-amount"]) / float(order["field-amount"]))
        addOrderList(order)
        if state == 'canceled':
            print("order", orderId, "canceled")
        elif state == 'partial-canceled':
            print("part dealed ", orderInfo["dealAmount"], " and canceled")
        elif state == ' partial-filled':
            if watiCount == tradeWaitCount:
                print("part dealed ", orderInfo["dealAmount"])
            else:
                print("part dealed ", orderInfo["dealAmount"], end=" ")
                sys.stdout.flush()
        elif state == 'filled':
            print("order", orderId, "complete deal")
        else:
            if watiCount == tradeWaitCount:
                print("timeout no deal")
            else:
                print("no deal", end=" ")
                sys.stdout.flush()
        return state
    else:
        print(orderId, "checkOrderStatus failed,try again.")
        checkOrderStatus(orderId, watiCount)


def trade(symbol, type, amount, price=0):
    if price == 0:
        price = getTradePrice(symbol, type)
    if type == TRADE_BUY:
        amount = getBuyAmount(price, 2)
    if amount < 0.1:
        return 'filled'
    orderId = makeOrder(symbol, type, price, amount)
    if orderId != "-1":
        watiCount = 0
        state = ''
        dealAmountBak = orderInfo["dealAmount"]
        while watiCount < (tradeWaitCount + 1) and state != 'filled':
            state = checkOrderStatus(orderId, watiCount)
            time.sleep(0.1)
            watiCount += 1
            if watiCount == tradeWaitCount and state != 'filled':
                if getTradePrice(symbol, type) == orderInfo["price"]:
                    watiCount -= 1
        if state != 'filled':
            state = cancelOrder(orderId)
            setDealAmount(dealAmountBak + orderInfo["dealAmount"])
        return state
    else:
        return 'failed'


def getCoinPrice(symbol):
    data = get_ticker(symbol)
    if data["status"] == 'ok':
        priceInfo[symbol]["buy"] = round(float(data["tick"]["ask"][0]), 5)
        priceInfo[symbol]["bid"] = round(float(data["tick"]["bid"][0]), 5)


def getTradePrice(symbol, type):
    getCoinPrice(symbol)
    if type == TRADE_BUY:
        return priceInfo[symbol]["buy"] + orderDiff
    else:
        return priceInfo[symbol]["bid"] - orderDiff


def writeLog(text=""):
    global orderInfo
    f = open(r'log.txt', 'a')
    if text == "":
        f.writelines(' '.join(
            ["\n", orderInfo["symbol"], orderInfo["type"], str(orderInfo["price"]), str(orderInfo["avgPrice"]),
             str(orderInfo["dealAmount"]),
             str(round(orderInfo["avgPrice"] * orderInfo["dealAmount"], 3)), str(fromTimeStamp(int(time.time())))]))
    else:
        f.writelines("\n" + text)
    f.close()


def getAccountInfo(symbol):
    print(u'---------------------------------------spot account info------------------------------------------------')
    myAccountInfo = get_balance("693874")
    if myAccountInfo["status"] == 'ok':
        data = fromDict(myAccountInfo, "data", "list")
        for sy in symbol:
            _sy = list(filter(lambda x: x["currency"] == sy, data))
            accountInfo[sy]["available"] = float(_sy[0]["balance"])
            accountInfo[sy]["freezed"] = float(_sy[1]["balance"])
            accountInfo[sy]["total"] = accountInfo[sy]["available"] + accountInfo[sy]["freezed"]
            print(sy.upper(), accountInfo[sy]["total"], "available", accountInfo[sy]["available"],
                  "freezed", accountInfo[sy]["freezed"])
    else:
        print("getAccountInfo Fail,Try again!")
        getAccountInfo(symbol)

# getAccountInfo([BALANCE_HT, BALANCE_USDT])
# getCoinPrice(SYMBOL_HT)
