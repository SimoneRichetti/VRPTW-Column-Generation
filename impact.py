b1 = b2 = b3 = bs = be = br = 1/3


def insertNode(route, node, position, s, arr, d, a):
    newRoute = route[:]
    newRoute.insert(position, node)
    newS = []; newArr = []
    for i in range(position):
        newS.append(s[i])
        newArr.append(arr[i])
    for i in range(position, len(newRoute)):
        newArr.append(newS[i-1] + d[newRoute[i-1], newRoute[i]])
        newS.append(max(newArr[i], a[i]))
    return newRoute, newS, newArr


def routeIsFeasible(route, a, b, s, d, q, Q):
    cap = sum([q[node] for node in route])
    if cap > Q:
        return False
    for i in range(len(route)):
        if not ((s[i] >= a[route[i]]) and (s[i] <= b[route[i]])):
            return False
    return True


def computeISIULD(posU, route, arr, s, a, b, d, Jminu):
    u = route[posU]
    posI = posU-1; posJ = posU+1
    i = route[posI]; j = route[posJ]
    IS = arr[posU] - a[u]
    IU = 1/(max([len(Jminu), 1])) * sum([max([b[n]-a[u]-d[u,n], b[u]-a[n]-d[u,n]]) \
                                for n in Jminu])
    c1 = (d[i,u] + d[u,j] - d[i,j])
    c2 = ((b[j]- (arr[posI] + d[i,j])) - \
                (b[j] - (arr[posU] + d[i,j])))
    c3 = (b[u] - (arr[posI] + d[i,u]))
    LD = b1*c1 + b2*c2 + b3*c3

    return IS, IU, LD


def computeImpact(IS, IU, LD, feasiblePositions):
    IR = sum(LD)/len(feasiblePositions)
    bestImpact = None
    bestPosition = None
    for i in range(len(feasiblePositions)):
        impact = IS[i] + IU[i] + IR
        if bestPosition == None or impact < bestImpact:
            bestImpact = impact
            bestPosition = feasiblePositions[i]

    return bestPosition, bestImpact


def computeRouteCost(route, d):
    cost = 0
    for i in range(len(route)-1):
        cost += d[route[i], route[i+1]]
    return cost


def initializePathsWithImpact(d, n, a, b, q, Q):
    J = list(range(1,n+1))
    routes = []
    costs = []

    while J:
        # Find furthest node from depot in J and initialize route with it
        far = -1
        max_dist = -1
        for j in J:
            if d[0,j] > max_dist:
                far = j
                max_dist = d[0,j]

        route = [0, far, n+1]
        arr = [0, d[0,far]]
        s = [0, max([a[far], arr[1]])]
        arr.append(s[1] + d[far,n+1])
        s.append(max(arr[2], a[n+1]))
        J.remove(far)

        feasible = J[:]

        while feasible:
            proposals = dict()
            for u in feasible:
                bestImpact = None
                bestPosition = None
                Jminu = J[:]
                Jminu.remove(u)
                feasiblePositions = []
                IS = IU = LD = []
                for pos in range(1, len(route)):
                    newRoute, newS, newArr = insertNode(route, u, pos, s, \
                                                        arr, d, a)
                    if routeIsFeasible(newRoute, a, b, newS, d, q, Q):
                        feasiblePositions.append(pos)
                        Is, Iu, Ld = computeISIULD(pos, newRoute, newArr, \
                                                    newS, a, b, d, Jminu)
                        IS.append(Is); IU.append(Iu); LD.append(Ld)

                if not feasiblePositions:
                    feasible.remove(u)
                else:
                    bestPosition, bestImpact = computeImpact(IS, IU, LD, \
                                                             feasiblePositions)
                    proposals[bestImpact] = (u, bestPosition)
                # END FOR
            # prendo miglior impact
            if proposals:
                nodeToInsert, insertPos = proposals[min(list(proposals.keys()))]
                # aggiungo nodo in posizione
                route, s, arr = insertNode(route, nodeToInsert, insertPos, s, \
                                            arr, d, a)
                # rimuovo nodo da J e da feasible
                feasible.remove(nodeToInsert)
                J.remove(nodeToInsert)
            # END WHILE

        routes.append(route)
        costs.append(computeRouteCost(route, d))
        # END WHILE
    print("Impact routes:\n", routes)
    return routes
