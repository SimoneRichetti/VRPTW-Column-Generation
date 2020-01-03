import gurobipy as gp
import numpy as np


def readData(filename):
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

    return vehicleNumber, capacity, data


def createDistanceMatrix(data):
    # TODO: arrotondare distanze a prima cifra decimale
    d = np.zeros((len(data), len(data)))
    for i in range(len(data)):
        for j in range(len(data)):
            p1 = np.array([float(data[i]["XCOORD."]), float(data[i]["YCOORD."])])
            p2 = np.array([float(data[j]["XCOORD."]), float(data[j]["YCOORD."])])
            d[i,j] = np.linalg.norm(p1-p2)
    return d


def createMasterProblem(a, costs, n, numberOfPaths):
    model = gp.Model("Master problem")
    vars = model.addVars(range(numberOfPaths), name="y",
                              vtype=gp.GRB.CONTINUOUS)
    model.setObjective(vars.prod(costs.tolist()), gp.GRB.MINIMIZE)
    # Constraints
    constraints = list()
    for i in range(1,n+1):
        a_ip = np.array([])
        for p in range(a.shape[0]):
            a_ip = np.append(a_ip, np.sum(a[p,i]))
        constraints.append(model.addConstr(vars.prod(a_ip.tolist()),
                            gp.GRB.EQUAL, 1))

    signConstraints = list()
    for j in range(numberOfPaths):
        signConstraints.append(model.addConstr(vars[j], gp.GRB.GREATER_EQUAL, 0))

    return model, constraints, signConstraints


if __name__ == '__main__':
    Kdim, Q, data = readData("r203.txt")    # Number of vehicles, capacity and
                                            # customers' informations
    n = 50  # number of customers

    # Consider only depot + 50 customers
    data = data[0:n+1]
    data.append(data[0]) # The depot is represented by two identical
                         # nodes: 0 and n+1
    data[-1]["CUST-NO."] = "51"

    d = createDistanceMatrix(data)

    numberOfPaths = 1
    c = np.array([])            # costs array
    # quando dovrò aggiungere matrici, usare la funzione np.append(a, matrice, axis=0)
    # e le matrici dovranno essere 1x52x52
    a = np.zeros((numberOfPaths,n+2, n+2))  # path matrix

    # To initialize we create a path that goes trough all the customers
    # in the order specified in the file. We can do this because the sum of all
    # the demands is less than the capacity of one vehicle
    cost = 0
    for i in range(0, n+1):
        a[0, i, i+1] = 1
        cost += d[i,i+1]
    c = np.append(c, cost)

    masterModel, masterConstraints, masterSignConstraints = \
        createMasterProblem(a, c, n, numberOfPaths)
    masterModel.write("MasterVRPTW.lp")
    masterModel.optimize()
    #for var in masterModel.getVars():
    #    print(var.varName, var.x)

    # Ricava variabili duali, crea pricing problem e passale al pricing problem
    pi_i = []
    #print("pi_i")
    for const in masterConstraints:
        #print(const.pi)
        pi_i.append(const.pi)

    pi_zero = []
    #print("pi_zero")
    for const in masterSignConstraints:
        #print(const.pi)
        pi_zero.append(const.pi)
