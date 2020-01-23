from utilities import *
from optimization import *
from impact import initializePathsWithImpact
from timeit import default_timer as timer


INSTANCE_FILENAME = "r203.txt"
PATH_FILENAME = "paths.txt"


if __name__ == '__main__':
    # Read data from file and create distance matrix
    n = 5  # number of customers
    Kdim, Q, x, y, q, a, b = readData(INSTANCE_FILENAME, n)
    d = createDistanceMatrix(x, y)

    print("Start")
    start = timer()

    # Initialize routes with IMPACT heuristic
    routes = initializePathsWithImpact(d, n, a, b)
    # TODO: change A in customers x path matrix, where a_ip is the number of
    # times that path p visits customer i
    A = np.zeros((1,n+2,n+2))
    A[0,0,-1] = 1
    c = np.array([0])
    for route in routes:
        newPath, newCost = getMatrixAndCostFromList(route, d, n)
        A = np.append(A, newPath, axis=0)
        c = np.append(c, newCost)
    rc = np.zeros((n+2,n+2))    # reduced costs
    iter = 1

    while True:
        print("Iter", iter)
        # Create master problem model
        masterModel, masterConstraints = createMasterProblem(A, c, n, Kdim)
        masterModel.optimize()

        pi_i = []
        for const in masterConstraints:
            pi_i.append(const.pi)

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
            routes.append(route)
            newPath, newCost = getMatrixAndCostFromList(route, d, n)
            A = np.append(A, newPath, axis=0)
            c = np.append(c, newCost)
        iter += 1

    end = timer()
    print("+++RESULTS+++")
    print("Time Elapsed:", end-start)
    print("Solution cost:", masterModel.getAttr("ObjVal"))
    vs = masterModel.getVars()
    for i in range(len(vs)):
        if vs[i].x == 1.:
            print(routes[i-1])
