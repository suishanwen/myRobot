import numpy as np
import time
import pylab as pl
x = [1, 2, 3, 4, 5]# Make an array of x values
y = [1, 4, 9, 16, 25]# Make an array of y values for each x value
pl.plot(x, y)# use pylab to plot x and y
pl.show()# show the plot on the screen
while True:
    x[4]=x[4]+1
    y[4]=y[4]+1
    time.sleep(1)