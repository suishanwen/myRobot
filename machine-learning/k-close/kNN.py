from numpy import *
import operator


def classify0(inX, dataSet, labels, k):
    dataSetSize = dataSet.shape[0]
    diffMat = tile(inX, (dataSetSize, 1)) - dataSet
    sqDiffMat = diffMat ** 2
    sqDistances = sqDiffMat.sum(axis=1)
    distances = sqDistances ** 0.5
    sortedDistIndicies = distances.argsort()
    classCount = {}
    for i in range(k):
        itemsLabel = labels[sortedDistIndicies[i]]
        classCount[itemsLabel] = classCount.get(itemsLabel, 0) + 1
        sortedClassCount = sorted(classCount.items(), key=operator.itemgetter(1), reverse=True)
    return sortedClassCount[0][0]


def file2matrix(filename):
    fr = open(filename)
    arrayOnlines = fr.readlines()
    numberOfLines = len(arrayOnlines)
    returnMat = zeros((numberOfLines, 2))
    classLabelVector = []

    index = 0
    for line in arrayOnlines:
        line = line.strip()
        listFromLine = line.split('|')
        returnMat[index, :] = listFromLine[0:2]
        classLabelVector.append(int(listFromLine[-1]))
        index += 1
    return returnMat, classLabelVector


group, labels = file2matrix("db1")
print(group)
print(labels)
rs=classify0([4833.15, 45029.84], group, labels, 1)
print(rs)
