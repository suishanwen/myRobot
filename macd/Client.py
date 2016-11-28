#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
# 客户端调用，用于查看API返回结果

import configparser
import time

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


def getMA(param):
    ms = int(time.time() * 1000)
    if type == "15min":
        ms -= param * 15 * 60 * 1000
    data = okcoinSpot.klines(symbol, type, param, ms)
    ma = 0
    if len(data) != param:
        raise Exception("抛出一个异常")
    for line in data:
        ma += line[4]
    return round(ma / param, 2)


trend = ""
trendBak = ""
while True:
    try:
        ma7 = getMA(7)
        ma30 = getMA(30)
        if ma7 >= ma30:
            trend = "up"
        else:
            trend = "down"
        if trendBak != "" and trendBak != trend:
            sendEmail("趋势发生改变")
        trendBak = trend
        print('ma7:%(ma7)s  ma30=%(ma30)s' % {'ma7': ma7, 'ma30': ma30})
    except Exception as err:
        print(err)
    time.sleep(5)
