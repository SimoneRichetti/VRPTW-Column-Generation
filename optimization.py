import numpy as np
import gurobipy as gp
import math
from utilities import *


def createMasterProblem(A, costs, n, vehicleNumber):
    model = gp.Model("Master problem")
    model.Params.OutputFlag = 0
    vars = model.addVars(A.shape[1], name="y",
                              vtype=gp.GRB.CONTINUOUS)
    model.setObjective(vars.prod(costs.tolist()), gp.GRB.MINIMIZE)
    # Constraints
    constraints = model.addConstrs(vars.prod(A[i,:].tolist()) == 1 for i in range(1,n+1))
    model.write("MasterModel.lp")

    return model, constraints



def subProblem(n, q, d, readyt, duedate, rc, Q):
    M = gp.GRB.INFINITY
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

    # Reduce max capacity to boost algorithm
    if sum(q) < Q:
        Q = sum(q)
    T = max(b)

    # Init necessary data structure
    f = list()  # paths cost data struct
    p = list()  # paths predecessor data struct
    f_tick = list()     # cost of the best path that does not pass for
                        # predecessor
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
    f_tick[0][0,0] = 0
    L = set()   # Node to explore
    L.add(0)

    # Implement bucket list for smart node extraction
    B = []
    for qu in range(Q):
        B.append([])
        for t in range(max(b)):
            B[-1].append([])

    # Algorithm
    while L:
        # Find best node to extract
        i = None
        for k in range(len(B)):
            for qtlist in B[k]:
                for node in qtlist:
                    if node in L:
                        nodeToExtract = qtlist.pop(qtlist.index(node))
                        break
        if not i:
            i = L.pop()
        else:
            L.remove(i)
        if i == n+1:
            continue

        # Explore all possible arcs (i,j)
        for j in range(1,n+2):
            if i == j:
                continue

            for q_tick in range(q[i], Q-q[j]):
                for t_tick in range(a[i], b[i]):
                    if True: # p[i][q_tick-q[i], t_tick-a[i]] != j:
                        if f[i][q_tick-q[i], t_tick-a[i]] < M:
                            for t in range(max([a[j], math.ceil(t_tick + d[i,j])]), b[j]):
                                if f[j][q_tick, t-a[j]]>f[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]:
                                    # update f
                                    f[j][q_tick, t-a[j]]=f[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]
                                    # update path that leads to node j
                                    paths[j][q_tick][t-a[j]] = paths[i][q_tick-q[i]][t_tick-a[i]] + [j]
                                    # update bucket list
                                    B[q_tick+q[j]][t].append(j)
                                    # Update predecessor
                                    p[j][q_tick, t-a[j]] = i
                                    L.add(j)
                                # If the path is suitable to be the alternative
                                # if p[j][q_tick, t-a[j]] != i and f_tick[j][q_tick, t-a[j]]>f[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]:
                                #     f_tick[j][q_tick, t-a[j]] = f[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]
                                #     paths_tick[j][q_tick][t-a[j]] = paths[i][q_tick-q[i]][t_tick-a[i]] + [j]
                    # else:       # if predecessor of i is j
                    #     if f_tick[i][q_tick-q[i], t_tick-a[i]] < M:
                    #         for t in range(max([a[j], math.ceil(t_tick + d[i,j])]), b[j]):
                    #             if f[j][q_tick, t-a[j]]>f_tick[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]:
                    #                 # update f, path and bucket
                    #                 f[j][q_tick, t-a[j]]=f_tick[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]
                    #                 paths[j][q_tick][t-a[j]] = paths_tick[i][q_tick-q[i]][t_tick-a[i]] + [j]
                    #                 B[q_tick+q[j]][t].append(j)
                    #                 p[j][q_tick, t-a[j]] = i
                    #                 L.add(j)
                    #             if p[j][q_tick, t-a[j]] != i and f_tick[j][q_tick, t-a[j]]>f_tick[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]:
                    #                 f_tick[j][q_tick, t-a[j]] = f_tick[i][q_tick-q[i], t_tick-a[i]]+rc[i,j]
                    #                 paths_tick[j][q_tick][t-a[j]] = paths_tick[i][q_tick-q[i]][t_tick-a[i]] + [j]

    # Return all the routes with negative cost
    routes = list()
    rcosts = list()
    qBest, tBest = np.where(f[n+1] < -1e-9)
    for i in range(len(qBest)):
        newRoute = [0] + paths[n+1][qBest[i]][tBest[i]]
        if not newRoute in routes:
            routes.append(newRoute)
            rcosts.append(f[n+1][qBest[i]][tBest[i]])

    print("New routes:", routes)
    return routes
