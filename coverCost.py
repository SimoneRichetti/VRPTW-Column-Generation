from utilities import *
from collections import Counter

ROUTES_FILENAME = "r203-5-customers-routes.txt"
if __name__ == "__main__":
    # Read CG generated routes
    lines = []
    with open(ROUTES_FILENAME, "r") as fin:
        lines = fin.readlines()
    INSTANCE_FILENAME = lines.pop(0).rstrip()
    allRoutes = [list(map(int, line[1:-2].split(", "))) for line in lines]
    n = int(ROUTES_FILENAME.split("-")[1])

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

    # Find route with best coverage/cost ratio and add it to the sol
    coverCost = [(len(routes[i])-2)/costs[i] for i in range(len(routes))]
    bestIndex = coverCost.index(max(coverCost))
    #print(routes[bestIndex], costs[bestIndex], coverCost[bestIndex])
    for node in routes[bestIndex][1:-1]:
        nodes.remove(node)
    sol = [routes[bestIndex]]
    solCost = costs[bestIndex]

    # Start loop
    while nodes:
        filteredRoutes = []
        filteredCosts = []
        for i in range(len(routes)):
            feasible = True
            for node in routes[i][1:-1]:
                if not node in nodes:
                    feasible = False
                    break
            if feasible:
                filteredRoutes.append(routes[i])
                filteredCosts.append(costs[i])

        filteredCoverCost = [(len(filteredRoutes[i])-2)/filteredCosts[i] for i in range(len(filteredRoutes))]
        bestIdx = filteredCoverCost.index(max(filteredCoverCost))
        sol.append(filteredRoutes[bestIdx])
        solCost += filteredCosts[bestIdx]
        for node in filteredRoutes[bestIdx][1:-1]:
            nodes.remove(node)
        routes = filteredRoutes[:]
        costs = filteredCosts[:]

    print("+++RESULTS+++")
    print("Solution cost:", solCost)
    print("Solution:", sol)
