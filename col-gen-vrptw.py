from utilities import *
from optimization import *
from impact import initializePathsWithImpact
from timeit import default_timer as timer

INSTANCE_FILENAME = "r203.txt"
PATH_FILENAME = "paths.txt"


if __name__ == '__main__':
    # Read data from file and create distance matrix
    n = 3  # number of customers
    Kdim, Q, x, y, q, a, b = readData(INSTANCE_FILENAME, n)
    d = createDistanceMatrix(x, y)

    print("Start")
    start = timer()

    # Initialize routes with IMPACT heuristic
    routes = initializePathsWithImpact(d, n, a, b)
    # A_pi = times that path p visits customer i
    A = np.zeros((n+2, len(routes)))
    c = np.zeros(len(routes))   # routes costs
    addRoutesToMaster(routes, A, c, d)

    rc = np.zeros((n+2,n+2))    # reduced costs
    iter = 1

    while True:
        print("Iter", iter)
        # Create master problem model
        masterModel, masterConstraints = createMasterProblem(A, c, n, Kdim)
        masterModel.optimize()

        pi_i = [const.pi for const in masterConstraints]

        for i in range(n+2):
            for j in range(n+2):
                if (i == 0) or (i == n+1):
                    rc[i,j] = d[i,j]
                else:
                    rc[i,j] = d[i,j] - pi_i[i-1]

        newRoutes = subProblem(n, q, d, a, b, rc, Q)
        if not newRoutes:
            break
        newMat = np.zeros((n+2, len(newRoutes)))
        newCosts = np.zeros(len(newRoutes))
        addRoutesToMaster(newRoutes, newMat, newCosts, d)
        routes += newRoutes
        c = np.append(c, newCosts)
        A = np.c_[A, newMat]
        iter += 1

    end = timer()
    print("+++RESULTS+++")
    print("Time Elapsed:", end-start)
    print("Solution cost:", masterModel.getAttr("ObjVal"))
    vs = masterModel.getVars()
    for i in range(len(vs)):
        if vs[i].x > 0.:
            print(vs[i].x, "  ", routes[i])
