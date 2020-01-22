import numpy as np
import gurobipy as gp
import math
from utilities import *


def createMasterProblem(A, costs, n, vehicleNumber):
    model = gp.Model("Master problem")
    model.Params.OutputFlag = 0
    vars = model.addVars(A.shape[0], name="y",
                              vtype=gp.GRB.CONTINUOUS) # vtype=gp.GRB.BINARY
    #yZero = model.addVar(name="Y0", vtype=gp.GRB.INTEGER)
    #yC = model.addVar(name="Yc", vtype=gp.GRB.INTEGER)
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

    """
    signConstraints = list()
    for p in range(A.shape[0]):
        signConstraints.append(model.addConstr(vars[p], gp.GRB.GREATER_EQUAL, 0))
    """

    return model, constraints



def subProblem(n, q, d, readyt, duedate, rc, Q):
    # Create f list with j matrix, each matrix has dimensions (Q-q_j, b_j-a_j)
    M = sum([d[i,j] for i in range(n+2) for j in range(n+2)])

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
    #print("Time windows optimized")

    f = list()
    p = list()
    f_tick = list()
    paths = []
    paths_tick = []
    for j in range(n+2):
        nodeList = []
        for qt in range(Q-q[j]):
            qtList = []
            for tm in range(b[j]-a[j]):
                qtList.append([])
            nodeList.append(qtList)
        paths.append(nodeList)
        paths_tick.append(nodeList)
        mat = np.zeros((Q-q[j], b[j] - a[j]))
        p.append(mat - 1)
        f.append(mat + M)
        f_tick.append(mat + M)

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


    #print("Necessary data structures initialized")

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
        #print("Extract node", i, flush=True)

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
                    #if p[i][q_tick-q[i], t_tick-a[i]] != j: # last node before i is not j
                    if True:
                        if f[i][q_tick-q[i], t_tick-a[i]] < M:
                            for t in range(max([a[j], math.ceil(t_tick + d[i,j])]), b[j]):
                                if f[j][q_tick, t-a[j]]>f[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]:
                                    # update f
                                    f[j][q_tick, t-a[j]]=f[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]
                                    # update path that leads to node j
                                    paths[j][q_tick][t-a[j]] = paths[i][q_tick-q[i]][t_tick-a[i]] + [j]
                                    # update buket list
                                    B[q_tick+q[j]][t].append(j)
                                    # update f'
                                    """if p[j][q_tick, t-a[j]] != i:
                                        f_tick[j][q_tick, t-a[j]] = f[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]
                                        # update path that leads to node j without passing from i
                                        paths_tick[j][q_tick][t-a[j]] = paths[i][q_tick-q[i]][t_tick-a[i]] + [j]"""
                                    # Update last node in path
                                    p[j][q_tick, t-a[j]] = i
                                    L.add(j)
                    """else:
                        if f_tick[i][q_tick-q[i], t_tick-a[i]] < M:
                            for t in range(max([a[j], math.ceil(t_tick + d[i,j])]), b[j]):
                                if f[j][q_tick, t-a[j]]>f_tick[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]:
                                    f[j][q_tick, t-a[j]]=f_tick[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]
                                    paths[j][q_tick][t-a[j]] = paths_tick[i][q_tick-q[i]][t_tick-a[i]] + [j]
                                    B[q_tick+q[j]][t].append(j)
                                    if p[j][q_tick, t-a[j]] != i:
                                        f_tick[j][q_tick, t-a[j]] = f_tick[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]
                                        paths_tick[j][q_tick][t-a[j]] = paths_tick[i][q_tick-q[i]][t_tick-a[i]] + [j]
                                    p[j][q_tick, t-a[j]] = i
                                    L.add(j)"""

    #print("end while")
    best = np.amin(f[n+1])
    if best >= -1e-9:
        return None, None
    qBest, tBest = np.where(f[n+1] == best)
    path = [0] + paths[n+1][qBest[-1]][tBest[-1]]
    print("New route:", path, ", cost:", best)
    return path, best
