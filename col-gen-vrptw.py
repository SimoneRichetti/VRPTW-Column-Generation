import gurobipy as gp
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
    # TODO: arrotondare distanze a prima cifra decimale
    d = np.zeros((n+2, n+2))
    for i in range(n+2):
        for j in range(n+2):
            p1 = np.array([x[i], y[i]])
            p2 = np.array([x[j], y[j]])
            d[i,j] = round(np.linalg.norm(p1-p2), 1)
    return d


def createMasterProblem(A, costs, n):
    model = gp.Model("Master problem")
    vars = model.addVars(A.shape[0], name="y",
                              vtype=gp.GRB.CONTINUOUS)
    model.setObjective(vars.prod(costs.tolist()), gp.GRB.MINIMIZE)
    # Constraints
    constraints = list()
    for i in range(1,n+1):      # for each customer
        a_ip = np.array([])
        for p in range(A.shape[0]):     # for each path
            # append to the list the number of times path p visits customer i
            a_ip = np.append(a_ip, np.sum(A[p,i]))
        constraints.append(model.addConstr(vars.prod(a_ip.tolist()),
                            gp.GRB.EQUAL, 1))

    signConstraints = list()
    for p in range(A.shape[0]):
        signConstraints.append(model.addConstr(vars[p], gp.GRB.GREATER_EQUAL, 0))

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

    for i in range(2, n+1):
        path = np.zeros((1,n+2,n+2))
        path[0,0,i] = 1
        path[0,i,-1] = 1
        a = np.append(a, path, axis=0)
        c = np.append(c, d[0,i] + d[i,-1])

    return a, c


def computeMaxCost():
    # TODO: Use distance mat. to find an equivalent to infinity for subproblem
    return gp.GRB.INFINITY


def elementaryShortestPath(d, pi, q, Q, a, b, n):
    M = computeMaxCost()
    rc = np.zeros((n+2,n+2))
    for i in range(n+2):
        for j in range(n+2):
            if (i==0) or (i==n+1):
                rc[i,j] = d[i,j]
            else:
                rc[i,j] = d[i,j] + pi[i-1]

    model = gp.Model("ESPModel")
    x_vars = model.addVars(n+2, n+2, vtype=gp.GRB.BINARY, name="x")
    s_vars = model.addVars(n+2, vtype=gp.GRB.CONTINUOUS, name="s")

    model.setObjective(gp.quicksum(x_vars[i,j]*rc[i,j] \
                                    for i in range(n+2) \
                                    for j in range(n+2)), \
                                    gp.GRB.MINIMIZE)
    # R0: capacity constraint
    model.addConstr(sum([q[i] * \
                    gp.quicksum(x_vars[i,j] for j in range(n+2)) \
                    for i in range(1,n+1)]) <= Q)
    # R1: depot start constraint
    model.addConstr(gp.quicksum(x_vars[0,j] for j in range(n+2)) == 1)
    # R2: depot finish constraint
    model.addConstr(gp.quicksum(x_vars[i,n+1] for i in range(n+2)) == 1)
    # R3-R53: flow costraints
    for h in range(1,n+1):
        model.addConstr(gp.quicksum(x_vars[i,h] for i in range(n+2)) - \
                        gp.quicksum(x_vars[h,j] for j in range(n+2)) == 0)

    # Time windows contraints
    for i in range(n+2):
        for j in range(n+2):
            if j!=i:
                model.addConstr(s_vars[i] + d[i,j] - M*(1-x_vars[i,j]) <= \
                                s_vars[j])

    # Service time constraints
    model.addConstrs(a[i] <= s_vars[i] for i in range(1,n+1))
    model.addConstrs(s_vars[i] <= b[i] for i in range(1,n+1))

    # Goodsense constraints:
    # Must not exist an arc that connects a customer with himself
    model.addConstr(gp.quicksum(x_vars[i,i] for i in range(n+2)) == 0)
    # No arc can enter in the first node
    model.addConstr(gp.quicksum(x_vars[i,0] for i in range(n+2)) == 0)
    # No arc can exist from the last node
    model.addConstr(gp.quicksum(x_vars[n+1, j] for j in range(n+2)) == 0)

    model.write("ESPModel.lp")
    model.optimize()

    print("Solution value: ", model.objVal)
    print("Selected arcs:")
    for i in range(n+2):
        for j in range(n+2):
            var = model.getVarByName("x["+str(i)+","+str(j)+"]")
            if(var.x == 1):
                print(var)

    return


if __name__ == '__main__':
    n = 50  # number of customers
    Kdim, Q, x, y, q, a, b = readData("r203.txt", n)

    d = createDistanceMatrix(x, y)
    # quando dovrò aggiungere matrici, usare la funzione np.append(a, matrice, axis=0)
    # e le matrici dovranno essere 1x52x52
    A, c = initializePaths(d)

    # TODO: If sign constraints are not used, delete them
    masterModel, masterConstraints, masterSignConstraints = \
        createMasterProblem(A, c, n)

    masterModel.write("MasterVRPTW.lp")
    masterModel.optimize()
    #for var in masterModel.getVars():
    #    print(var.varName, var.x)

    pi_i = []
    #print("pi_i")
    for const in masterConstraints:
        #print(const.pi)
        pi_i.append(const.pi)

    # TODO: if this dual variable is not used, delete it
    pi_zero = []
    #print("pi_zero")
    for const in masterSignConstraints:
        #print(const.pi)
        pi_zero.append(const.pi)

    newPath = elementaryShortestPath(d, pi_i, q, Q, a, b, n)
