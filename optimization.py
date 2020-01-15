import numpy as np
import gurobipy as gp
from utilities import *


def createMasterProblem(A, costs, n, vehicleNumber):
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

    model.addConstr(gp.quicksum(vars) <= vehicleNumber)

    signConstraints = list()
    for p in range(A.shape[0]):
        signConstraints.append(model.addConstr(vars[p], gp.GRB.GREATER_EQUAL, 0))

    return model, constraints, signConstraints


def computeMaxCost(d, a, b, n):
    # TODO: Use distance mat. to find an equivalent to infinity for subproblem
    return max([b[i] + d[i,j] - a[j] for i in range(n+2) for j in range(n+2)])


def setESPModelFO(model, x_vars, pi, n, d):
    rc = np.zeros((n+2,n+2))
    for i in range(n+2):
        for j in range(n+2):
            if (i==0) or (i==n+1):
                rc[i,j] = d[i,j]
            else:
                rc[i,j] = d[i,j] - pi[i-1]
    model.setObjective(gp.quicksum(x_vars[i,j]*rc[i,j] for i in range(n+2) \
                                                       for j in range(n+2)), \
                       gp.GRB.MINIMIZE)
    return


def createESPModel(d, pi, q, Q, a, b, n):
    M = computeMaxCost(d, a, b, n)
    model = gp.Model("ESPModel")
    x_vars = model.addVars(n+2, n+2, vtype=gp.GRB.BINARY, name="x")
    s_vars = model.addVars(n+2, vtype=gp.GRB.CONTINUOUS, name="s")

    setESPModelFO(model, x_vars, pi, n, d)

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
    model.addConstrs(s_vars[i] >= a[i] for i in range(1,n+1))
    model.addConstrs(s_vars[i] <= b[i] for i in range(1,n+1))

    # Goodsense constraints:
    # Must not exist an arc that connects a customer with himself
    model.addConstr(gp.quicksum(x_vars[i,i] for i in range(n+2)) == 0)
    # No arc can enter in the first node
    model.addConstr(gp.quicksum(x_vars[i,0] for i in range(n+2)) == 0)
    # No arc can exit from the last node
    model.addConstr(gp.quicksum(x_vars[n+1,j] for j in range(n+2)) == 0)

    # model.write("ESPModel.lp")
    return model
