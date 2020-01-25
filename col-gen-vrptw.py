from utilities import *
from optimization import *
from impact import initializePathsWithImpact
from timeit import default_timer as timer

INSTANCE_FILENAME = "r203.txt"
PATH_FILENAME = "paths.txt"

### TODOS ###
# Add 2-cycle elimination
# Add branch and bound
# Delete unused functions
# Use numpy where possible
# (Optional) Plot routes
######


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

        pi_i = [const.pi for const in masterConstraints.values()]

        for i in range(n+2):
            for j in range(n+2):
                if (i == 0) or (i == n+1):
                    rc[i,j] = d[i,j]
                else:
                    rc[i,j] = d[i,j] - pi_i[i-1]

        newRoutes = subProblem(n, q, d, a, b, rc, Q)
        if not newRoutes:
            break
        for route in newRoutes:
            if route in routes:
                print("\nERROR: DUPLICATE PATH\n")
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
    sec = int(end-start)
    min = int(sec / 60)
    sec %=  60
    print("Time Elapsed:", min, "minutes", sec, "s")
    print("Solution cost:", masterModel.getAttr("ObjVal"))
    vs = masterModel.getVars()
    for i in range(len(vs)):
        if vs[i].x > 0.:
            print(round(vs[i].x, 3), "   ", routes[i])
