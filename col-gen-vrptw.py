from utilities import *
from optimization import *
from impact import initializePathsWithImpact


INSTANCE_FILENAME = "r203.txt"
PATH_FILENAME = "paths.txt"


if __name__ == '__main__':
    # Read data from file and create distance matrix
    n = 5  # number of customers
    Kdim, Q, x, y, q, a, b = readData(INSTANCE_FILENAME, n)
    d = createDistanceMatrix(x, y)

    # Initialize routes with IMPACT heuristic
    routes = initializePathsWithImpact(d, n, a, b)
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
        #for var in masterModel.getVars():
            #print(var)
        #input()

        pi_i = []
        for const in masterConstraints:
            #print(const.pi)
            pi_i.append(const.pi)


        for i in range(n+2):
            for j in range(n+2):
                if (i == 0) or (i == n+1):
                    rc[i,j] = d[i,j]
                else:
                    rc[i,j] = d[i,j] - pi_i[i-1]
        #print(rc)
        if np.amin(rc) >= -1e-9:
            break
        """
        # TODO: if this dual variable is not used, delete it
        pi_zero = []
        #print("pi_zero")
        for const in masterSignConstraints:
            #print(const.pi)
            pi_zero.append(const.pi)
        """
        newRoute, newRC = subProblem(n, q, d, a, b, rc, Q)
        if not newRoute:
            break
        routes.append(newRoute)
        newPath, newCost = getMatrixAndCostFromList(newRoute, d, n)
        A = np.append(A, newPath, axis=0)
        c = np.append(c, newCost)
        iter += 1


    print("I finished bitch")
    print(masterModel.getVars())
    vs = masterModel.getVars()
    for i in range(len(vs)):
        if vs[i].x == 1.:
            print(routes[i-1])




"""
ESPModel = createESPModel(d, pi_i, q, Q, a, b, n)
ESPModel.optimize()
for i in range(n+2):
    for j in range(n+2):
        var = ESPModel.getVarByName("x["+str(i)+","+str(j)+"]")
        if(var.x == 1):
            # selectedVars.append(var)
            # newPath[i,j] = 1
            print(var)
"""
