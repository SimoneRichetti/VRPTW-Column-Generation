import numpy as np
import gurobipy as gp
import math
from utilities import *


def createMasterProblem(A, costs, n, vehicleNumber):
    model = gp.Model("Master problem")
    model.Params.OutputFlag = 0
    y = model.addMVar(shape=A.shape[1], vtype=gp.GRB.CONTINUOUS, name="y")
    model.setObjective(costs @ y, gp.GRB.MINIMIZE)
    # Constraints
    model.addConstr(A @ y == np.ones(A.shape[0]))
    model.write("MasterModel.lp")

    return model


def reduceTimeWindows(n, d, readyt, duedate):
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
            newa = int(max([a[k], minArrPred, minArrNext]))
            if newa != a[k]:
                update = True
            a[k] = newa

            # Due date
            maxDepPred = max([a[k],
                            max([b[i] + d[i,k] for i in range(n+1) if i!=k])])
            maxDepNext = max([a[k],
                            max([b[j] - d[k,j] for j in range(1,n+2) if j!=k])])
            newb = int(min([b[k], maxDepPred, maxDepNext]))
            if newb != b[k]:
                update = True
            b[k] = newb
    return a,b


def subProblem(n, q, d, readyt, duedate, rc, Q):
    M = gp.GRB.INFINITY     # 1e+100
    # Time windows reduction
    a,b = reduceTimeWindows(n, d, readyt, duedate)
    # Reduce max capacity to boost algorithm
    if sum(q) < Q:
        Q = sum(q)
    T = max(b)

    # Init necessary data structure
    f = list()  # paths cost data struct
    p = list()  # paths predecessor data struct
    f_tk = list()     # cost of the best path that does not pass for
                      # predecessor (we'll call it alternative path)
    paths = []
    paths_tk = []
    for j in range(n+2):
        paths.append([])
        paths_tk.append([])
        for qt in range(Q-q[j]):
            paths[-1].append([])
            paths_tk[-1].append([])
            for tm in range(b[j]-a[j]):
                paths[-1][-1].append([])
                paths_tk[-1][-1].append([])
        mat = np.zeros((Q-q[j], b[j] - a[j]))
        p.append(mat - 1)
        f.append(mat + M)
        f_tk.append(mat + M)
    f[0][0,0] = 0
    f_tk[0][0,0] = 0
    L = set()   # Node to explore
    L.add(0)

    # Algorithm
    while L:
        i = L.pop()
        if i == n+1:
            continue

        # Explore all possible arcs (i,j)
        for j in range(1,n+2):
            if i == j:
                continue
            for q_tk in range(q[i], Q-q[j]):
                for t_tk in range(a[i], b[i]):
                    if p[i][q_tk-q[i], t_tk-a[i]] != j:
                        if f[i][q_tk-q[i], t_tk-a[i]] < M:
                            for t in range(max([a[j], int(t_tk+d[i,j])]),\
                                                b[j]):
                                if f[j][q_tk, t-a[j]]> \
                                   f[i][q_tk-q[i],t_tk-a[i]]+rc[i,j]:
                                    # if the current best path is suitable to
                                    # become the alternative path
                                    if p[j][q_tk, t-a[j]] != i \
                                       and p[j][q_tk, t-a[j]] != -1 \
                                       and f[j][q_tk, t-a[j]] < M \
                                       and f[j][q_tk,t-a[j]]<f_tk[j][q_tk,t-a[j]]:
                                        f_tk[j][q_tk,t-a[j]] = f[j][q_tk,t-a[j]]
                                        paths_tk[j][q_tk][t-a[j]] = \
                                                paths[j][q_tk][t-a[j]][:]
                                    # update f
                                    f[j][q_tk,t-a[j]] = \
                                            f[i][q_tk-q[i],t_tk-a[i]] + rc[i,j]
                                    # update path that leads to node j
                                    paths[j][q_tk][t-a[j]] = \
                                            paths[i][q_tk-q[i]][t_tk-a[i]] + [j]
                                    # Update predecessor
                                    p[j][q_tk, t-a[j]] = i
                                    L.add(j)
                                # if the path is suitable to be the alternative
                                elif p[j][q_tk, t-a[j]] != i \
                                    and p[j][q_tk, t-a[j]] != -1 \
                                    and f_tk[j][q_tk, t-a[j]] > \
                                            f[i][q_tk-q[i],t_tk-a[i]]+rc[i,j]:
                                    f_tk[j][q_tk,t-a[j]] = \
                                            f[i][q_tk-q[i],t_tk-a[i]]+rc[i,j]
                                    paths_tk[j][q_tk][t-a[j]] = \
                                            paths[i][q_tk-q[i]][t_tk-a[i]]+[j]
                    else:       # if predecessor of i is j
                        if f_tk[i][q_tk-q[i], t_tk-a[i]] < M:
                            for t in range(max([a[j],int(t_tk+d[i,j])]), \
                                                b[j]):
                                if f[j][q_tk,t-a[j]] > \
                                        f_tk[i][q_tk-q[i],t_tk-a[i]]+rc[i,j]:
                                    # if the current best path is suitable to
                                    # become the alternative path
                                    if p[j][q_tk, t-a[j]] != i \
                                        and p[j][q_tk, t-a[j]] != -1 \
                                        and f[j][q_tk, t-a[j]] < M \
                                        and f[j][q_tk,t-a[j]] < \
                                                f_tk[j][q_tk,t-a[j]]:
                                        f_tk[j][q_tk,t-a[j]] = f[j][q_tk,t-a[j]]
                                        paths_tk[j][q_tk][t-a[j]] = \
                                                paths[j][q_tk][t-a[j]][:]
                                    # update f, path and bucket
                                    f[j][q_tk,t-a[j]] = \
                                        f_tk[i][q_tk-q[i],t_tk-a[i]] + rc[i,j]
                                    paths[j][q_tk][t-a[j]] = \
                                        paths_tk[i][q_tk-q[i]][t_tk-a[i]] + [j]
                                    p[j][q_tk,t-a[j]] = i
                                    L.add(j)
                                # if the alternative path of i is suitable to
                                # be the alternate of j
                                elif p[j][q_tk, t-a[j]] != i \
                                     and p[j][q_tk, t-a[j]] != -1 \
                                     and f_tk[j][q_tk,t-a[j]] > \
                                            f_tk[i][q_tk-q[i],t_tk-a[i]]+rc[i,j]:
                                    f_tk[j][q_tk, t-a[j]] = \
                                        f_tk[i][q_tk-q[i],t_tk-a[i]]+rc[i,j]
                                    paths_tk[j][q_tk][t-a[j]] = \
                                        paths_tk[i][q_tk-q[i]][t_tk-a[i]] + [j]

    # Return all the routes with negative cost
    routes = list()
    rcosts = list()
    qBest, tBest = np.where(f[n+1] < -1e-9)
    for i in range(len(qBest)):
        newRoute = [0] + paths[n+1][qBest[i]][tBest[i]]
        if not newRoute in routes:
            routes.append(newRoute)
            rcosts.append(f[n+1][qBest[i]][tBest[i]])
    print("New routes:", routes, flush=True)
    return routes
