from utilities import *
from collections import Counter
import os
from sys import exit


def coverCostHeuristic(bestIndex, allRoutes, allCosts, allCoverCost):
    nodes = set(range(1,n+1))
    routes = allRoutes[:]
    costs = allCosts[:]
    coverCost = allCoverCost[:]

    for node in routes[bestIndex][1:-1]:
        nodes.remove(node)
    sol = [routes[bestIndex]]
    solCost = costs[bestIndex]

    # Start loop
    while nodes:
        filteredRoutes = []
        filteredCosts = []
        filteredCoverCost = []
        for i in range(len(routes)):
            feasible = True
            for node in routes[i][1:-1]:
                if not node in nodes:
                    feasible = False
                    break
            if feasible:
                filteredRoutes.append(routes[i])
                filteredCosts.append(costs[i])
                filteredCoverCost.append(coverCost[i])
        if not filteredRoutes:
            return None

        bestIdx = filteredCoverCost.index(max(filteredCoverCost))
        sol.append(filteredRoutes[bestIdx])
        solCost += filteredCosts[bestIdx]
        for node in filteredRoutes[bestIdx][1:-1]:
            nodes.remove(node)
        routes = filteredRoutes[:]
        costs = filteredCosts[:]

    return (sol, solCost)


if __name__ == "__main__":
    # Take in input instance and number of costumers
    INSTANCE_NAME, INSTANCE_FILENAME, n = readInstanceN()
    ROUTES_FILENAME = os.path.join("routes", \
                            INSTANCE_NAME+"-"+str(n)+"-customers-routes.txt")
    if not os.path.exists(ROUTES_FILENAME):
        print("No routes generated for this instance and number of customers.")
        print("Run: 'python col-gen-vrptw.py' and input desired instance and" +\
                "number of customers.")
        print("Exit")
        exit(1)


    # Read CG generated routes
    lines = []
    with open(ROUTES_FILENAME, "r") as fin:
        lines = fin.readlines()
    allRoutes = [list(map(int, line[1:-2].split(", "))) for line in lines[1:]]

    # Discard all routes that visit a node more than one time
    nodes = set(range(1,n+1))
    routes = []
    for route in allRoutes:
        occ = Counter(route)
        if max(occ.values()) == 1:
            routes.append(route)

    # Create distance matrix and routes costs
    Kdim, Q, x, y, q, a, b = readData(INSTANCE_FILENAME, n)
    d = createDistanceMatrix(x, y)
    costs = []
    for route in routes:
        cost = 0.
        for i in range(len(route)-1):
            cost += d[route[i], route[i+1]]
        costs.append(cost)

    # Find coverage/cost ratio off the routes
    coverCost = [(len(routes[i])-2)/costs[i] for i in range(len(routes))]
    idxBestCoverCost = sorted(coverCost, reverse = True)
    # if len(idxBestCoverCost) > 300:
    #    idxBestCoverCost =idxBestCoverCost[:300]
    # Find indexes of the 10 paths with the best cover cost
    idxBestCoverCost = set([coverCost.index(idxBestCoverCost[i]) \
                            for i in range(len(idxBestCoverCost))])

    solutions = []
    solutionCosts = []
    for bestIndex in idxBestCoverCost:
        info = coverCostHeuristic(bestIndex, routes, costs, coverCost)
        if info:
            solutions.append(info[0])
            solutionCosts.append(info[1])

    solCost = min(solutionCosts)
    sol = solutions[solutionCosts.index(solCost)]
    print("+++RESULTS+++")
    print("Solution cost:", solCost)
    print("Solution:", sol)
