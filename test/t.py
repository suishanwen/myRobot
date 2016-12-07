from util.MyUtil import fromDict, fromTimeStamp, sendEmail
from api.OkcoinSpotAPI import OKCoinSpot
import time, sys, configparser
# 读取配置文件
config = configparser.ConfigParser()
config.read("../key.ini")

# 初始化apikey，secretkey,url
apikey = config.get("okcoin", "apikey")
secretkey = config.get("okcoin", "secretkey")
okcoinRESTURL = 'www.okcoin.cn'  # 请求注意：国内账号需要 修改为 www.okcoin.cn

# 现货API
okcoinSpot = OKCoinSpot(okcoinRESTURL, apikey, secretkey)
import pylab as pl
def getMA(param):
    ms = int(time.time() * 1000)
    type="1week"
    if type == "15min":
        ms -= param * 15 * 60 * 1000
    elif type == "1min":
        ms -= param * 1 * 60 * 1000
    elif type == "1week":
        ms -= param * 1 * 7 * 24 * 60 * 60 * 1000
    data = okcoinSpot.klines("btc_cny", type, param, ms)
    print()
    ma = 0
    if len(data) != param:
        raise Exception("等待数据...")
    for line in data:
        ma += line[4]
    return round(ma / param, 2)
x=[]
y=[]
ma3=getMA(3)
print(ma3)
print(x)
print(y)
pl.plot(x, y)# use pylab to plot x and y
pl.show()# show the plot on the screen