import numpy as np


def readData(filename, n):
    stream = ""
    with open(filename, "r") as file:
        stream = file.readlines()
    if stream == "":
        print("Error in reading file")

    vehicleNumber, capacity = [int(i) for i in stream[4].split()]
    fields = stream[7].split()

    data = list()
    for i in range(9, len(stream)):
        if stream[i] == "\n":
            continue

        val = stream[i].split()
        if len(val) != len(fields):
            print("Error in reading data")
            continue

        customer = dict(zip(fields, val))
        data.append(customer)

    # Consider only depot + 50 customers
    data = data[0:n+1]
    data.append(data[0]) # The depot is represented by two identical
                         # nodes: 0 and n+1
    data[-1]["CUST-NO."] = "51"

    x = []; y = []; q = []; a = []; b = []
    for customer in data:
        x.append(int(customer["XCOORD."]))
        y.append(int(customer["YCOORD."]))
        q.append(int(customer["DEMAND"]))
        a.append(int(customer["READY-TIME"]))
        b.append(int(customer["DUE-DATE"]))

    return vehicleNumber, capacity, x, y, q, a, b


def createDistanceMatrix(x, y):
    n = len(x)
    d = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            p1 = np.array([x[i], y[i]])
            p2 = np.array([x[j], y[j]])
            d[i,j] = round(np.linalg.norm(p1-p2), 1)
    return d


def getMatrixAndCostFromList(nodes, d, n):
    path = np.zeros((1,n+2,n+2))
    cost = 0
    for i in range(len(nodes)-1):
        path[0,nodes[i],nodes[i+1]] = 1
        cost += d[nodes[i], nodes[i+1]]
    return path, cost


def addRoutesToMaster(routes, mat, costs, d):
    for i in range(len(routes)):
        cost = 0.
        for j in range(len(routes[i])):
            if j != len(routes[i])-1:
                cost += d[routes[i][j], routes[i][j+1]]
            mat[routes[i][j],i] += 1
        costs[i] = cost
