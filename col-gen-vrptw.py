from utilities import *
from optimization import *
from impact import initializePathsWithImpact, computeRouteCost
from time import process_time
import os


### TODOS ###
# Create Timer to clean the code
# Move file writes of results in a dedicated function
# Take instance and customer number from CLI
# See if it is possible to extend master model each iteration instead of
#   recreate it each time (model.addVar(..., *column = ...*))
# Use numpy where possible (use np array for x, y, a, b, ... if possible)
#   -> fun. readData
# Plot routes
######


if __name__ == '__main__':
    INSTANCE_NAME, INSTANCE_FILENAME, n = readInstanceN()

    # Read data from file and create distance matrix
    Kdim, Q, x, y, q, a, b = readData(INSTANCE_FILENAME, n)
    d = createDistanceMatrix(x, y)
    print("Number of customers:", n, "\n")
    print("Start")
    start = process_time()

    # Initialize routes with IMPACT heuristic and dummy paths
    impactSol = initializePathsWithImpact(d, n, a, b, q, Q)
    routes = impactSol[:]
    #print("Impact solution:", routes)
    impactCost = sum([computeRouteCost(route, d) for route in routes])
    print("Impact cost:", impactCost)
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
        # Compute reduced costs
        constr = masterModel.getConstrs()
        pi_i = [0.] + [const.pi for const in constr] + [0.]
        for i in range(n+2):
            for j in range(n+2):
                rc[i,j] = d[i,j] - pi_i[i]

        if not np.where(rc < -1e-9):
            break

        newRoutes = subProblem(n, q, d, a, b, rc, Q)
        # Exit condition
        if not newRoutes:
            break
        for route in newRoutes:
            if route in routes:
                print("\nDUPLICATE PATH\n", flush=True)
                break
        # Add new routes to master problem
        newMat = np.zeros((n, len(newRoutes)))
        newCosts = np.zeros(len(newRoutes))
        addRoutesToMaster(newRoutes, newMat, newCosts, d)
        routes += newRoutes
        c = np.append(c, newCosts)
        A = np.c_[A, newMat]
        iter += 1
        # Print partial time
        sc = int(process_time()-start)
        mn = int(sc / 60)
        sc %=  60
        print("Partial time:", mn, "min", sc, "s")

    end = process_time()
    print("+++RESULTS+++")
    sec = int(end-start)
    min = int(sec / 60)
    sec %=  60
    print("Time Elapsed:", min, "min", sec, "s")
    print("Impact solution cost:", impactCost)
    print("Exact solution cost:", masterModel.getAttr("ObjVal"))

    # Write results on file in directory "results"
    if not os.path.exists(os.path.join(os.getcwd(), "results")):
        os.mkdir(os.path.join(os.getcwd(), "results"))
    filenameOut = os.path.join("results", \
                               "results-"+INSTANCE_NAME+"-"+str(n)+".txt")
    fout = open(filenameOut, "w")
    fout.write("Impact solution cost: " + str(impactCost) + "\n")
    fout.write("Impact solution: " + str(impactSol) + "\n")
    fout.write("Exact solution cost: "+str(masterModel.getAttr("ObjVal"))+"\n")
    for i in range(len(routes)):
        var = masterModel.getVarByName("y["+str(i)+"]")
        if var.x > 0.:
            print(round(var.x, 3), "   ", routes[i])
            fout.write(str(round(var.x, 3)) + "   " + str(routes[i]) + "\n")
    fout.close()

    # Write generated routes on file for CoverCost heuristic
    if not os.path.exists(os.path.join(os.getcwd(), "routes")):
        os.mkdir(os.path.join(os.getcwd(), "routes"))
    outfile = os.path.join("routes", \
                            INSTANCE_NAME+"-"+str(n)+"-customers-routes.txt")
    with open(outfile, "w") as fout:
        fout.write(INSTANCE_NAME + "\n")
        for route in routes:
            fout.write(str(route) + "\n")
