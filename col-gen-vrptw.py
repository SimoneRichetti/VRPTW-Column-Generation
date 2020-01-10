from utilities import *
from optimization import *

INSTANCE_FILENAME = "r203.txt"
PATH_FILENAME = "paths.txt"

if __name__ == '__main__':
    n = 50  # number of customers
    Kdim, Q, x, y, q, a, b = readData(INSTANCE_FILENAME, n)

    d = createDistanceMatrix(x, y)
    # quando dovrò aggiungere matrici, usare la funzione np.append(a, matrice, axis=0)
    # e le matrici dovranno essere 1x52x52
    A, c = initializeDummyPaths(d, n)

    # TODO: If sign constraints are not used, delete them
    masterModel, masterConstraints, masterSignConstraints = \
        createMasterRelaxedProblem(A, c, n)
    masterModel.optimize()

    pi_i = []
    for const in masterConstraints:
        pi_i.append(const.pi)
    """
    # TODO: if this dual variable is not used, delete it
    pi_zero = []
    #print("pi_zero")
    for const in masterSignConstraints:
        #print(const.pi)
        pi_zero.append(const.pi)
    """
    generatePathsModel, x_vars = createESPModel(d, pi_i, q, Q, a, b, n)
    generatePaths(generatePathsModel, x_vars, n, PATH_FILENAME)

    # initialize A with paths.txt
    A, c = initializePathsFromFile(d, n, PATH_FILENAME)

    # masterConstraints.append(masterModel.addConstr(gp.quicksum(model.getVars()) <= Kdim))
    #masterModel.write("MasterVRPTW.lp")

    # start cycle!
