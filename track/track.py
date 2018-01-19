import urllib.request
import ssl, re, time, requests

coinList = [{"name": "Bitcoin", "version": "1.1.10"},
            {"name": "Bitcoin Cash", "version": "1.1.8"},
            {"name": "Dash", "version": "1.1.5"},
            {"name": "Dogecoin", "version": "1.1.5"},
            {"name": "Ethereum", "version": "1.0.22"},
            {"name": "Komodo", "version": "1.1.5"},
            {"name": "Litecoin", "version": "1.1.9"},
            {"name": "Stratis", "version": "1.1.5"},
            {"name": "Zcash", "version": "1.1.5"},
            {"name": "Ripple", "version": "1.0.3"},
            {"name": "PoSW Coin", "version": "1.1.7"},
            {"name": "Ark", "version": "0.1.1"},
            {"name": "Ubiq", "version": "1.0.22"},
            {"name": "Expanse", "version": "1.0.20"},
            {"name": "PIVX", "version": "1.1.12"},
            {"name": "Stealthcoin", "version": "1.1.10"},
            {"name": "Vertcoin", "version": "1.1.10"},
            {"name": "Viacoin", "version": "1.1.10"},
            {"name": "Neo", "version": "1.1.1"},
            {"name": "Bitcoin-Gold", "version": "1.1.16"},
            {"name": "Stellar", "version": "1.1.1"},
            {"name": "DigiByte", "version": "1.1.17"},
            {"name": "Hshare", "version": "1.1.17"},
            {"name": "Qtum", "version": "1.1.17"}
            ]

_info = """<b><a href="$URL$" target="_blank">$NAME$($VERSION$)</a>&nbsp; &nbsp;</b>"""
_rank = """    <small style="color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif; box-sizing: border-box; font-size: 13.600000381469727px;">
        <span class="label label-success"
              style="box-sizing: border-box; display: inline; padding: 0.2em 0.6em 0.3em; font-size: 10.199999809265137px; font-weight: 700; line-height: 1; color: rgb(255, 255, 255); text-align: center; white-space: nowrap; vertical-align: baseline; border-top-left-radius: 0.25em; border-top-right-radius: 0.25em; border-bottom-right-radius: 0.25em; border-bottom-left-radius: 0.25em; background-color: rgb(92, 184, 92);">Rank $RANK$</span>
    </small>
    <span style="color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 16px;">&nbsp;</span>"""
_mineable = """    <small style="color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif; box-sizing: border-box; font-size: 13.600000381469727px;">
        <span class="label label-warning"
              style="box-sizing: border-box; display: inline; padding: 0.2em 0.6em 0.3em; font-size: 10.199999809265137px; font-weight: 700; line-height: 1; color: rgb(255, 255, 255); text-align: center; white-space: nowrap; vertical-align: baseline; border-top-left-radius: 0.25em; border-top-right-radius: 0.25em; border-bottom-right-radius: 0.25em; border-bottom-left-radius: 0.25em; background-color: rgb(240, 173, 78);">Mineable</span>
    </small>
    <span style="color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 16px;">&nbsp;</span>"""
_coin = """    <small style="color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif; box-sizing: border-box; font-size: 13.600000381469727px;">
        <span class="label label-warning"
              style="box-sizing: border-box; display: inline; padding: 0.2em 0.6em 0.3em; font-size: 10.199999809265137px; font-weight: 700; line-height: 1; color: rgb(255, 255, 255); text-align: center; white-space: nowrap; vertical-align: baseline; border-top-left-radius: 0.25em; border-top-right-radius: 0.25em; border-bottom-right-radius: 0.25em; border-bottom-left-radius: 0.25em; background-color: rgb(240, 173, 78);">Coin</span>
    </small>"""
_price = """<p><span class="text-large2" data-currency-value=""
         style="box-sizing: border-box; font-size: 24px; line-height: 1.1; color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif;">$PRICE$</span><span
        style="color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif; font-size: 16px; background-color: rgb(255, 255, 255);">&nbsp;</span><span
        class="details-text-medium" data-currency-code=""
        style="box-sizing: border-box; font-size: 0.9em; color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif;">USD</span><br>
</p>"""
_summary = """<div class="coin-summary-item col-xs-6  col-md-3"
     style="font-size: 16px; box-sizing: border-box; position: relative; min-height: 1px; padding: 0; float: left; width: 175.828125px; color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif;">
    <div class="coin-summary-item-header" style="box-sizing: border-box;">
        <h3 class="details-text-medium"
            style="box-sizing: border-box; font-size: 0.9em; margin: 0; font-family: inherit; line-height: 1.1; color: inherit; padding: 10px; border-width: 1px 0; border-top-style: solid; border-top-color: rgb(221, 221, 221); border-bottom-style: solid; border-bottom-color: rgb(221, 221, 221); white-space: nowrap;">
            Market Cap</h3>
    </div>
    <div class="coin-summary-item-detail details-text-medium"
         style="box-sizing: border-box; padding: 10px; font-size: 0.9em;"><span data-currency-market-cap=""
                                                                                data-usd=""
                                                                                style="box-sizing: border-box;"><span
            data-currency-value="" style="box-sizing: border-box;">$MARKET_CAP$</span>&nbsp;<span
            data-currency-code="" style="box-sizing: border-box;">USD</span>&nbsp;</span><br
            style="box-sizing: border-box;">
    </div>
</div>
<div class="coin-summary-item col-xs-6  col-md-3"
     style="font-size: 16px; box-sizing: border-box; position: relative; min-height: 1px; padding: 0; float: left; width: 175.828125px; color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif;">
    <div class="coin-summary-item-header" style="box-sizing: border-box;">
        <h3 class="details-text-medium"
            style="box-sizing: border-box; font-size: 0.9em; margin: 0; font-family: inherit; line-height: 1.1; color: inherit; padding: 10px; border-width: 1px 0; border-top-style: solid; border-top-color: rgb(221, 221, 221); border-bottom-style: solid; border-bottom-color: rgb(221, 221, 221); white-space: nowrap;">
            Volume (24h)</h3>
    </div>
    <div class="coin-summary-item-detail details-text-medium"
         style="box-sizing: border-box; padding: 10px; font-size: 0.9em;"><span data-currency-volume=""
                                                                                data-usd=""
                                                                                style="box-sizing: border-box;"><span
            data-currency-value="" style="box-sizing: border-box;">$VOLUME$</span>&nbsp;<span
            data-currency-code="" style="box-sizing: border-box;">USD</span>&nbsp;</span><br
            style="box-sizing: border-box;">
    </div>
</div>
<div class="coin-summary-item col-xs-6  col-md-3"
     style="font-size: 16px; box-sizing: border-box; position: relative; min-height: 1px; padding: 0; float: left; width: 175.828125px; color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif;">
    <div class="coin-summary-item-header" style="box-sizing: border-box;">
        <h3 class="details-text-medium"
            style="box-sizing: border-box; font-size: 0.9em; margin: 0; font-family: inherit; line-height: 1.1; color: inherit; padding: 10px; border-width: 1px 0; border-top-style: solid; border-top-color: rgb(221, 221, 221); border-bottom-style: solid; border-bottom-color: rgb(221, 221, 221); white-space: nowrap;">
            Circulating Supply</h3>
    </div>
    <div class="coin-summary-item-detail details-text-medium"
         style="box-sizing: border-box; padding: 10px; font-size: 0.9em;">$SUPPLY$
    </div>
</div>
<p><span class="details-text-medium" data-currency-code=""
         style="box-sizing: border-box; font-size: 0.9em; color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif;"></span>
</p>
<div class="coin-summary-item col-xs-6  col-md-3 "
     style="font-size: 16px; box-sizing: border-box; position: relative; min-height: 1px; padding: 0; float: left; width: 175.828125px; color: rgb(51, 51, 51); font-family:Helvetica Neue, Helvetica, Arial, sans-serif;">
    <div class="coin-summary-item-header" style="box-sizing: border-box;">
        <h3 class="details-text-medium"
            style="box-sizing: border-box; font-size: 0.9em; margin: 0; font-family: inherit; line-height: 1.1; color: inherit; padding: 10px; border-width: 1px 0; border-top-style: solid; border-top-color: rgb(221, 221, 221); border-bottom-style: solid; border-bottom-color: rgb(221, 221, 221); white-space: nowrap;">
            Max Supply</h3>
    </div>
    <div class="coin-summary-item-detail details-text-medium"
         style="box-sizing: border-box; padding: 10px; font-size: 0.9em;">$MAX_SUPPLY$
    </div>
</div>
<p><br></p><p><br></p><p><br></p><p><br></p><p><br></p><p><br></p>"""
context = ssl._create_unverified_context()


def httpGet(url):
    insideException = True
    data = ''
    while insideException:
        try:
            res = urllib.request.urlopen(url, timeout=10, context=ssl._create_unverified_context())
            data = res.read().decode('utf-8')
            insideException = False
        except Exception as err:
            time.sleep(1)
    return data


def httpPost(url, data):
    insideException = True
    while insideException:
        try:
            res = urllib.request.urlopen(url, data=data, timeout=10, context=ssl._create_unverified_context())
            data = res.read().decode('utf-8')
            insideException = False
        except Exception as err:
            print(err)
    return data


def getCoinHtml(coin):
    html = _info.replace("$NAME$", coin["name"]).replace("$URL$", coin["url"]).replace("$VERSION$",
                                                                                       coin[
                                                                                           "version"]) + _rank.replace(
        "$RANK$",
        coin[
            "rank"])
    if coin["mineable"] == 1:
        html += _mineable
    html += _coin + _price.replace(
        "$PRICE$", coin["price"]) + _summary.replace("$MARKET_CAP$", coin["marketCap"]).replace("$VOLUME$",
                                                                                                coin["volume"]).replace(
        "$SUPPLY$",
        coin["supply"]).replace(
        "$MAX_SUPPLY$", coin["maxSupply"])
    return html.replace("\n", "")


def saveNote(content):
    url = 'http://allinbitcoin:8051/sw/api/note/edit'
    data = {
        "content": content,
        "editTime": 1515049856000,
        "id": 73,
        "ip": "36.110.123.238",
        "postTime": 1515048068000,
        "poster": "myRobot",
        "recommend": 1,
        "summary": "Ledger Wallet  Coin Comparsion",
        "tag": "Ledger",
        "title": "Ledger Wallet  Coin Comparsion"
    }
    try:
        r = requests.post(url, json=data)
        print(r.text)
    except Exception as err:
        print(err)


def getCoinInfo():
    newHtml = ''
    for coin in coinList:
        url = 'https://coinmarketcap.com/currencies/' + coin["name"].lower().replace(" ", "-")
        html = httpGet(url)
        html = html[html.index('Cryptocurrency Market Capitalizations'):html.index('Coin</span></small>')]
        rank = re.findall(r"Rank (.+?)</span>", html)[0]
        mineable = len(re.findall(r"Mineable", html))
        price = re.findall(r'<span class="text-large2" data-currency-value>(.+?)</span>', html)[0]
        marketInfo = re.findall(r'<span data-currency-value>(.+?)</span>', html)
        marketCap = marketInfo[0]
        volume = marketInfo[1]
        supply = ""
        maxSupply = ""
        supplyInfo = re.findall(r'<div class="coin-summary-item-detail details-text-medium">\s*\t*\n*(.*)\s*\t*\n*',
                                html)
        if len(supplyInfo) == 4 or len(supplyInfo) == 5:
            supply = supplyInfo[len(supplyInfo) - 2]
            maxSupply = supplyInfo[len(supplyInfo) - 1]
        elif len(supplyInfo) == 3:
            supply = supplyInfo[2]
        coin["url"] = url
        coin["rank"] = rank
        coin["mineable"] = mineable
        coin["price"] = "$" + price
        coin["marketCap"] = "$" + marketCap
        coin["volume"] = "$" + volume
        coin["supply"] = supply
        coin["maxSupply"] = maxSupply
        coin["html"] = getCoinHtml(coin)
        newHtml += coin["html"]
        print(coin)
    saveNote(newHtml)


getCoinInfo()
