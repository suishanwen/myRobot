#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
import sys, importlib
sys.path.append("/home/python")
importlib.reload(sys)

import time
import common.OKClient as OKClient
import common.BTCCClient as BTCCClient


def brick():
    print("brick")

# OKClient.showAccountInfo()
# BTCCClient.showAccountInfo()
# BTCCClient.getCoinPrice("btc_cny","buy")
# BTCCClient.getTradePrice("btc_cny","buy")
# BTCCClient.getCoinNum("btc_cny")
orderId=BTCCClient.makeOrder("btccny","buy",100,1)
print(orderId)
BTCCClient.cancelOrder("btccny",1103822078)

# while True:
#     try:
#         brick()
#     except Exception as err:
#         print(err)
#     time.sleep(0.5)
