#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
import sys, importlib
sys.path.append("/home/python")
importlib.reload(sys)

import time
import common.OKClient as OKClient


def brick():
    print("brick")

OKClient.showAccountInfo()
while True:
    try:
        brick()
    except Exception as err:
        print(err)
    time.sleep(0.5)
