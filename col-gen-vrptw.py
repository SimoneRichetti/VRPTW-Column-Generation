from utilities import *
from optimization import *
from impact import initializePathsWithImpact
from timeit import default_timer as timer

INSTANCE_FILENAME = "r203.txt"
PATH_FILENAME = "paths.txt"

### THIS MORNING
# Commit & push
# Try with 25 customers
# Study BB


### TODOS ###
# Count vehicle capacity in IMPACT path creation
# Add branch and bound
# Create timer and print partial times each iteration
# See if it is possible to extend master model each iteration instead of
#   recreate it each time (model.addVar(..., *column = ...*))
# Use numpy where possible (use np array for x, y, a, b, ... if possible)
#   -> fun. readData
# (Optional) Plot routes
######


if __name__ == '__main__':
    # Read data from file and create distance matrix
    n = 5     # number of customers
    Kdim, Q, x, y, q, a, b = readData(INSTANCE_FILENAME, n)
    d = createDistanceMatrix(x, y)
    print("Number of customers:", n, "\n")
    print("Start")
    start = timer()

    # Initialize routes with IMPACT heuristic
    routes = initializePathsWithImpact(d, n, a, b)
    for i in range(1,n+1):
         routes.append([0,i,n+1])
    # A[i,p] = times that path p visits customer i
    A = np.zeros((n, len(routes)))
    c = np.zeros(len(routes))   # routes costs
    addRoutesToMaster(routes, A, c, d)

    rc = np.zeros((n+2,n+2))    # reduced costs
    iter = 1

    while True:
        print("Iter", iter, flush=True)
        # Create master problem model
        masterModel = createMasterProblem(A, c, n, Kdim)
        masterModel.optimize()

        constr = masterModel.getConstrs()[:-1]

        pi_i = [0] + [const.pi for const in constr] + [0]

        for i in range(n+2):
            for j in range(n+2):
                rc[i,j] = d[i,j] - pi_i[i]

        newRoutes = subProblem(n, q, d, a, b, rc, Q)
        if not newRoutes:
            break
        for route in newRoutes:
            if route in routes:
                print("\nERROR: DUPLICATE PATH\n", flush=True)
                break

        newMat = np.zeros((n, len(newRoutes)))
        newCosts = np.zeros(len(newRoutes))
        addRoutesToMaster(newRoutes, newMat, newCosts, d)
        routes += newRoutes
        c = np.append(c, newCosts)
        A = np.c_[A, newMat]
        iter += 1
        sc = int(timer()-start)
        mn = int(sc / 60)
        sc %=  60
        print("Partial time:", mn, "min", sc, "s")

    end = timer()
    print("+++RESULTS+++")
    sec = int(end-start)
    min = int(sec / 60)
    sec %=  60
    print("Time Elapsed:", min, "min", sec, "s")
    print("Solution cost:", masterModel.getAttr("ObjVal"))
    for i in range(len(routes)):
        var = masterModel.getVarByName("y["+str(i)+"]")
        if var.x > 0.:
            print(round(var.x, 3), "   ", routes[i])
