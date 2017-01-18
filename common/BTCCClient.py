#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
import api.BTCCAPI as btcchina
from util.MyUtil import fromDict, fromTimeStamp, sendEmail
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
    print(myAccountInfo)
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
    if myAccountInfo["profile"]:
        balance = fromDict(myAccountInfo, "balance")
        frozen = fromDict(myAccountInfo, "frozen")
        print(u"RMB", round(float(frozen["cny"]["amount"]) + float(balance["cny"]["amount"]), 2), "available",
              balance["cny"]["amount"], "freezed", frozen["cny"]["amount"])
        print(u"BTC", balance["btc"]["amount"], "freezed", frozen["btc"]["amount"])
        print(u"LTC", balance["ltc"]["amount"], "freezed", frozen["ltc"]["amount"])
    else:
        print("showAccountInfo Fail,Try again!")
        showAccountInfo()
