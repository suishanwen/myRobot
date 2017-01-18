#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
import api.BTCCAPI as btcchina
from util.MyUtil import fromDict, fromTimeStamp, sendEmail, hasattr
import time, sys, configparser

# read config
configBase = configparser.ConfigParser()
config0 = configparser.ConfigParser()
configBase.read("../key.ini")
config0.read("config.ini")

# init apikey,secretkey,url
access_key = configBase.get("btcc", "access_key")
secret_key = configBase.get("btcc", "secret_key")
bc = btcchina.BTCChina(access_key, secret_key)
# getConfig
tradeWaitCount = int(config0.get("trade", "tradeWaitCount"))
orderDiff = float(config0.get("trade", "orderDiff"))

# global variable
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
    myAccountInfo = bc.get_account_info()
    if hasattr(myAccountInfo, "profile"):
        balance = fromDict(myAccountInfo, "balance")
        if symbol == "btccny":
            return float(balance["btc"]["amount"])
        else:
            return float(balance["ltc"]["amount"])
    else:
        print("getCoinNum Fail,Try again!")
        getCoinNum(symbol)


def getCoinPrice(symbol, type):
    if symbol == "btccny":
        result = bc.get_market_depth2()
        if hasattr(result, "market_depth"):
            bid = result["market_depth"]["bid"]
            ask = result["market_depth"]["ask"]
            if type == "buy":
                return round(float(bid[0]["price"]), 2)
            else:
                return round(float(ask[0]["price"]), 2)
        else:
            getCoinPrice(symbol, type)


def getTradePrice(symbol, type):
    if symbol == "btccny":
        result = bc.get_market_depth2()
        if hasattr(result, "market_depth"):
            bid = result["market_depth"]["bid"]
            ask = result["market_depth"]["ask"]
            if type == "buy":
                return round(float(bid[0]["price"]) + orderDiff, 2)
            else:
                return round(float(ask[0]["price"]) - orderDiff, 2)
        else:
            getTradePrice(symbol, type)


def makeOrder(symbol, type, price, amount):
    print(
        u'\n---------------------------------------------spot order--------------------------------------------------')
    result = bc.trade(price, amount, type, symbol)
    if isinstance(result,int):
        setPrice(price)
        print("OrderId", result, symbol, type, price, amount, "  ", fromTimeStamp(int(time.time())))
        return result
    else:
        print("order failed！", symbol, type, price, amount)
        global orderInfo
        print(orderInfo)
        return "-1"


def cancelOrder(symbol, orderId):
    print(u'\n-----------------------------------------spot cancel order----------------------------------------------')
    result = bc.cancel(orderId, symbol)
    if result:
        print(u"order", str(orderId), "canceled")
    else:
        print(u"order", orderId, "not canceled or cancel failed！！！")
    status = checkOrderStatus(symbol, orderId)
    if status != "closed" and status != "cancelled":  # not canceled or cancel failed(part dealed) continue cancel
        cancelOrder(symbol, orderId)
    return status


def addOrderList(order):
    global orderList
    orderList = list(filter(lambda orderIn: orderIn["order_id"] != order["order_id"], orderList))
    if float(order["amount_original"])-float(order["amount"]) > 0:
        orderList.append(order)


def checkOrderStatus(symbol, orderId, watiCount=0):
    global tradeWaitCount
    orderResult = bc.get_orders(orderId,symbol)
    print(orderResult)
    if hasattr(orderResult,"order"):
        order = orderResult["order"]
        if hasattr(order,"id"):
            orderId = order["id"]
            status = order["status"]
            setDealAmount(round(float(order["amount_original"])-float(order["amount"]),2))
            setAvgPrice(order["avg_price"])
            addOrderList(order)
            if status == "cancelled":
                print("order", orderId, "canceled")
            elif status == 0:
                if watiCount == tradeWaitCount:
                    print("timeout no deal")
                else:
                    print("no deal", end=" ")
                    sys.stdout.flush()
            elif status == "open":
                global orderInfo
                if watiCount == tradeWaitCount:
                    print(orderInfo["dealAmount"], "dealed ")
                else:
                    print(orderInfo["dealAmount"],"dealed " , end=" ")
                    sys.stdout.flush()
            elif status == "closed":
                print("order", orderId, "complete deal")
            elif status == "pending ":
                print("order", orderId, "canceling")
            return status
    else:
        print(orderId, " order not found")
        return "error"


def trade(symbol, type, amount, price=0):
    global tradeWaitCount, orderInfo, orderDiff
    if price == 0:
        price = getTradePrice(symbol, type)
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
        while watiCount < (tradeWaitCount + 1) and status != "closed":
            status = checkOrderStatus(symbol, orderId, watiCount)
            time.sleep(0.5)
            watiCount += 1
            if watiCount == tradeWaitCount and status != "closed":
                if getTradePrice(symbol, type) == orderInfo["price"]:
                    watiCount -= 1
        if status != "closed":
            status = cancelOrder(symbol, orderId)
            setDealAmount(dealAmountBak + orderInfo["dealAmount"])
        return status
    else:
        return "error"


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
    # {
    #     'profile': {'username': 'suishanwen', 'trade_password_enabled': True, 'otp_enabled': False, 'trade_fee': 0,
    #                 'trade_fee_cnyltc': 0, 'trade_fee_btcltc': 0, 'daily_btc_limit': 10, 'daily_ltc_limit': 400,
    #                 'btc_deposit_address': '1JpeoUD2oRahEADGVmiHFQZMJLBKfJsb69',
    #                 'btc_withdrawal_address': '3MncEptY5qi1Ryzt89rxrvSeimq3BSdTDh',
    #                 'ltc_deposit_address': 'LYUm7CTE3fwQjMJDFpsvjEmmxEmGPP5asm', 'ltc_withdrawal_address': '',
    #                 'api_key_permission': 7, 'id_verify': 1
    #                 },
    #     'balance': {
    #         'btc': {'currency': 'BTC', 'symbol': '฿', 'amount': '0.00000000', 'amount_integer': '0',
    #                 'amount_decimal': 8},
    #         'ltc': {'currency': 'LTC', 'symbol': 'Ł', 'amount': '0.00000000', 'amount_integer': '0',
    #                 'amount_decimal': 8},
    #         'cny': {'currency': 'CNY', 'symbol': '¥', 'amount': '378.29395', 'amount_integer': '37829395',
    #                 'amount_decimal': 5}
    #     },
    #     'frozen': {
    #         'btc': {'currency': 'BTC', 'symbol': '฿', 'amount': '0.00000000', 'amount_integer': '0',
    #                 'amount_decimal': 8},
    #         'ltc': {'currency': 'LTC', 'symbol': 'Ł', 'amount': '0.00000000', 'amount_integer': '0',
    #                 'amount_decimal': 8},
    #         'cny': {'currency': 'CNY', 'symbol': '¥', 'amount': '20110.22010', 'amount_integer': '2011022011',
    #                 'amount_decimal': 5}
    #     },
    #     'loan': {
    #         'btc': {'currency': 'BTC', 'symbol': '฿', 'amount': '0.00000000', 'amount_integer': '0',
    #                 'amount_decimal': 8},
    #         'cny': {'currency': 'CNY', 'symbol': '¥', 'amount': '0.00000', 'amount_integer': '0', 'amount_decimal': 5}
    #     }
    # }
    print(u'---------------------------------------spot account info------------------------------------------------')
    myAccountInfo = bc.get_account_info()
    print(myAccountInfo)
    if hasattr(myAccountInfo, "profile"):
        balance = fromDict(myAccountInfo, "balance")
        frozen = fromDict(myAccountInfo, "frozen")
        print(u"RMB", round(float(frozen["cny"]["amount"]) + float(balance["cny"]["amount"]), 2), "available",
              balance["cny"]["amount"], "freezed", frozen["cny"]["amount"])
        print(u"BTC", balance["btc"]["amount"], "freezed", frozen["btc"]["amount"])
        print(u"LTC", balance["ltc"]["amount"], "freezed", frozen["ltc"]["amount"])
    else:
        print("showAccountInfo Fail,Try again!")
        showAccountInfo()
