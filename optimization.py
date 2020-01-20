import numpy as np
import gurobipy as gp
import math
from utilities import *


def createMasterProblem(A, costs, n, vehicleNumber):
    model = gp.Model("Master problem")
    vars = model.addVars(A.shape[0], name="y",
                              vtype=gp.GRB.CONTINUOUS) # vtype=gp.GRB.BINARY
    # model.addVar(Y0, integer)     vedi paper desrocher
    # model.addVar(Yc, integer)
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


def subProblem(n, q, d, readyt, duedate, pi_i, pi_zero, Q):
    # Create f list with j matrix, each matrix has dimensions (Q-q_j, b_j-a_j)
    M = sum([d[i,j] for i in range(n+2) for j in range(n+2)])
    f = list()

    # Time windows reduction
    a = readyt[:]; b = duedate[:]
    update = True
    while update:
        update = False
        for k in range(1,n+1):
            # Ready Time
            minArrPred = min([b[k], \
                            min([a[i] + d[i,k] for i in range(n+1) if i!=k])])
            minArrNext = min([b[k], \
                            min([a[j] - d[k,j] for j in range(1,n+2) if j!=k])])
            newa = math.floor(max([a[k], minArrPred, minArrNext]))
            if newa != a[k]:
                update = True
            a[k] = newa

            # Due date
            maxDepPred = max([a[k],
                            max([b[i] + d[i,k] for i in range(n+1) if i!=k])])
            maxDepNext = max([a[k],
                            max([b[j] - d[k,j] for j in range(1,n+2) if j!=k])])
            newb = math.ceil(min([b[k], maxDepPred, maxDepNext]))
            if newb != b[k]:
                update = True
            b[k] = newb
    print("Time windows optimized")

    for j in range(n+2):
        mat = np.zeros((Q-q[j], b[j] - a[j]))
        mat += M
        f.append(mat)
    f[0][0,0] = 0
    L = set()
    L.add(0)

    if sum(q) < Q:
        Q = sum(q)

    B = []
    for qu in range(Q):
        B.append([])
        for t in range(max(b)):
            B[-1].append([])

    rc = np.zeros((n+2,n+2))
    for i in range(n+2):
        for j in range(n+2):
            if (i == 0) or (i == n+1):
                rc[i,j] = d[i,j]
            else:
                rc[i,j] = d[i,j] - pi_i[i-1]
    print("Necessary data structures initialized")
    
    while L:
        nodeToExtract = None
        for i in range(len(B)):
            bq = B[i]
            for qtlist in bq:
                for node in qtlist:
                    if node in L:
                        nodeToExtract = node
                        break
        i = nodeToExtract
        if not nodeToExtract:
            i = L.pop()
        else:
            L.remove(nodeToExtract)
        print("Extract node", i)

        # io qui scrivo tutto quello che vuoi e così troviamo il costo del
        # percorso...ma come lo trovo il percorso?
        # Ad ogni elemento di f, ovvero ad ogni costo, è associato un percorso
        # che lo ha generato. Ne possiamo tenere conto in una struttura dati a
        # parte.
        if i == n+1:
            continue
        for j in range(1,n+2):
            if i == j:
                continue
            #print("Exploring node", j)
            for q_tick in range(q[i], Q-q[j]):
                for t_tick in range(a[i], b[i]):
                    if f[i][q_tick-q[i], t_tick-a[i]] < M:
                        for t in range(max([a[j], math.ceil(t_tick + d[i,j])]), b[j]):
                            if f[j][q_tick, t-a[j]] > \
                                f[i][q_tick-q[i], t_tick-a[i]] + rc[i,j]:
                                f[j][q_tick, t-a[j]] = \
                                    f[i][q_tick-q[i], t_tick-a[i]] + rc[i,j]
                                B[q_tick+q[j]][t].append(j)
                                L.add(j)

    print("end while")
    input()

    return f
