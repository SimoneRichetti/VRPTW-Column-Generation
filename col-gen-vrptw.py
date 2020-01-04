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


def createMasterProblem(a, costs, n):
    model = gp.Model("Master problem")
    vars = model.addVars(range(a.shape[0]), name="y",
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
    for j in range(a.shape[0]):
        signConstraints.append(model.addConstr(vars[j], gp.GRB.GREATER_EQUAL, 0))

    return model, constraints, signConstraints

"""
Create some dummy feasible paths for initializing the master problem. For each
customer, create a path that starts from the depot, visits the customer and
returns to the depot. This violates the maximum number oh vehicles, but actually
we don't have a constraint about that.
"""
def initializePaths(d):
    a = np.zeros((1,n+2, n+2))          # path matrix
    a[0,0,1] = 1
    a[0,1,-1] = 1
    c = np.array([d[0,1] + d[1, -1]])   # costs array

    for i in range(1, n+1):
        path = np.zeros((1,n+2,n+2))
        path[0,0,i] = 1
        path[0,i,-1] = 1
        a = np.append(a, path, axis=0)
        c = np.append(c, d[0,i] + d[i,-1])

    return a, c


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
    # quando dovrò aggiungere matrici, usare la funzione np.append(a, matrice, axis=0)
    # e le matrici dovranno essere 1x52x52
    a, c = initializePaths(d)

    masterModel, masterConstraints, masterSignConstraints = \
        createMasterProblem(a, c, n)
    masterModel.write("MasterVRPTW.lp")
    masterModel.optimize()
    #for var in masterModel.getVars():
    #    print(var.varName, var.x)

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

    # newPath = subProblem(data, pi_i, pi_zero)
