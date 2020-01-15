from utilities import *
from optimization import *
from impact import initializePathsWithImpact


INSTANCE_FILENAME = "r203.txt"
PATH_FILENAME = "paths.txt"


if __name__ == '__main__':
    # Read data from file and create distance matrix
    n = 50  # number of customers
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

    # Create master problem model
    masterModel, masterConstraints, masterSignConstraints = \
        createMasterProblem(A, c, n, Kdim)

    masterModel.optimize()
    for var in masterModel.getVars():
        print(var)
    input()

    pi_i = []
    for const in masterConstraints:
        print(const.pi)
        pi_i.append(const.pi)
    """
    # TODO: if this dual variable is not used, delete it
    pi_zero = []
    #print("pi_zero")
    for const in masterSignConstraints:
        #print(const.pi)
        pi_zero.append(const.pi)
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
