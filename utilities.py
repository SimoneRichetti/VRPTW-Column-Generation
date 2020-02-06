import numpy as np
from sys import exit
import os


def readInstanceN():
    # Take in input instance name
    print("Instance name: [r|c|rc][NNN]")
    INSTANCE_NAME = None
    try:
        INSTANCE_NAME = input()
    except Exception as e:
        print("Invalid instance. Exit."); exit(1)
    if INSTANCE_NAME.endswith(".txt"):
        INSTANCE_NAME = INSTANCE_NAME[:-4]
    INSTANCE_FILENAME = os.path.join("solomon-instances", INSTANCE_NAME+".txt")
    if not INSTANCE_NAME or not os.path.exists(INSTANCE_FILENAME):
        print("Instance does not exists. Exit."); exit(1)

    # Take in input customers number
    print("Select number of costumers (1-100):")
    n = None
    try:
        n = int(input())
    except Exception as e:
        print("Invalid number of costumers. Exit."); exit(1)
    if not n or n < 1 or n > 100:
        print("Invalid number of costumers. Exit."); exit(1)
    return INSTANCE_NAME, INSTANCE_FILENAME, n


def readData(filename, n):
    stream = ""
    with open(filename, "r") as file:
        stream = file.readlines()
    if stream == "":
        print("Error in reading file")
    else:
        print("Read file", filename)

    vehicleNumber, capacity = [int(i) for i in stream[4].split()]
    fields = ("CUST-NO.", "XCOORD.", "YCOORD.", "DEMAND", "READY-TIME", \
                "DUE-DATE", "SERVICE-TIME")
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
        for j in range(i+1,n):
            p1 = np.array([x[i], y[i]])
            p2 = np.array([x[j], y[j]])
            d[i,j] = d[j,i] = int(round(np.linalg.norm(p1-p2)))
    return d


def addRoutesToMaster(routes, mat, costs, d):
    for i in range(len(routes)):
        cost = d[routes[i][0],routes[i][1]]
        for j in range(1,len(routes[i])-1):
            cost += d[routes[i][j], routes[i][j+1]]
            mat[routes[i][j]-1,i] += 1
        costs[i] = cost
