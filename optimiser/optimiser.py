from ortools.linear_solver import pywraplp
import numpy as np
import json

resources = ['emeralds'] + ["ore", "wood", "fish", "crops"]


def optimise_upgrades(territories):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    solver.SetNumThreads(6)
    if not solver:
        raise RuntimeError("Solver not created.")

    with open('data/resource_upgrades.json') as f:
        upgrades = json.load(f)
    with open('data/upgrades.json') as f:
        upgrade_costs = json.load(f)

    # Create resource categories
    categories = {}
    category_counter = {}
    for u in upgrades:
        categories[u] = []
        category_counter[u] = []
    for t in territories:
        territories[t]['categories'] = {}
        for u in upgrades:
            territories[t]['categories'][u] = {}
            res = upgrades[u]["bonus_resources"]
            terr_res = [territories[t]['production'][r] for r in res]
            c = dict(zip(res, terr_res))
            if c not in categories[u]:
                categories[u].append(c)
                category_counter[u].append([])
            index = categories[u].index(c)
            territories[t]['categories'][u]['index'] = index
            # Grouping in groups with sizes following fibonacci!!!
            # If you're interested, look up the Zeckendorf theorem.
            # 1,1,2,3,5,8,13,21,34
            groups = category_counter[u][index]
            if len(groups) <= 2:
                groups.append(1)
            elif groups[-3] + groups[-2] < groups[-1] + 1:
                groups.append(1)
            else:
                groups[-1] += 1
            territories[t]['categories'][u]['group'] = len(groups) - 1

    # print(category_counter)
    # print(categories)
    for u in upgrades:
        n = sum(len(x) for x in category_counter[u])
        print(f"number of groups in upgrade type {u}: {n}")
    # for t in territories:
    #     print(territories[t]['categories'])


    # Decision variables: x[u, c, g, r, e] = 1 if territory in category c, group g gets upgrade u with rate r and efficiency e
    x = {}
    nk = {k: (len(v['costs']), len(v['costs'][0])) for k, v in upgrades.items()}

    res_prod = {res:[] for res in resources}
    res_cost = {res:[] for res in resources}

    for u in upgrades:  # upgrade type u
        for c, prod in enumerate(categories[u]):  # category index c
            counter = category_counter[u][c]
            for g, n in enumerate(counter):  # fibonacci group g with n territories
                for r in range(nk[u][0]):  # rate upgrade
                    for e in range(nk[u][1]):  # efficiency upgrade
                        x[u, c, g, r, e] = solver.IntVar(0, 1, f"x_{u}_{c}_{g}_{r}_{e}")
                # Select exactly one upgrade level
                solver.Add(solver.Sum(x[u, c, g, r, e] for r in range(nk[u][0]) for e in range(nk[u][1])) == 1)

                # Generate production bonuses and associated costs
                for res in upgrades[u]["bonus_resources"]:  # iterate through resources boosted by the upgrade
                    p = prod[res]
                    # print(u, c, g, res, p)
                    if p > 0:
                        res_prod[res].append(n*p)  # base production (number of territories in group) x production
                        for r in range(nk[u][0]):  # rate upgrade
                            for e in range(nk[u][1]):  # efficiency upgrade
                                bonus = p*upgrades[u]['bonus'][r][e]
                                costs = upgrades[u]['costs'][r][e]
                                res_prod[res].append(n*bonus*x[u, c, g, r, e])
                                for ress, cost in costs.items():
                                    res_cost[ress].append(n*cost*x[u, c, g, r, e])
                # Account for storage requirements (tbh this is now fucked up a bit but storages don't matter anyways)
                # Also we still only look at storage requirements from production. Costs would make this multiplicative
                pmax = max(prod.values())
                for r in range(nk[u][0]):  # rate upgrade
                    for e in range(nk[u][1]):  # efficiency upgrade
                        bonus = pmax*upgrades[u]['bonus'][r][e]
                        storage_cost = 0
                        for terr in territories.values():
                            if terr['categories'][u]['index'] == c and terr['categories'][u]['group'] == g:
                                if u == "Emeralds":
                                    level = terr["upgrades"].get("emeraldStorage",0)
                                else:
                                    level = terr["upgrades"].get("resourceStorage",0)
                                storage_cost += get_storage_cost(pmax + bonus, u, hq=(terr['distance']==0), level=level)
                        if storage_cost > 0:
                            if u == "Emeralds":
                                res_cost['wood'].append(storage_cost*x[u, c, g, r, e])
                            else:
                                res_cost['wood'].append(storage_cost*x[u, c, g, r, e])

    # Add costs for additional upgrades
    for territory in territories.values():
        for u,v in territory['upgrades'].items():
            res = upgrade_costs[u]["resource"]
            cost = upgrade_costs[u]['costs'][v]
            res_cost[res].append(cost)


    res_prod_sum = {}
    res_cost_sum = {}
    extra_surplus = {'emeralds':2000, "ore":25000, "crops":25000, "fish":25000, "wood":25000}
    for res in resources:
        res_prod_sum[res] = solver.Sum(res_prod[res])
        res_cost_sum[res] = solver.Sum(res_cost[res])
        solver.Add(res_prod_sum[res] >= res_cost_sum[res] + extra_surplus[res])
        # solver.Add(res_prod_sum[res] <= res_cost_sum[res] + extra_surplus[res] + 10000)


    # Objective: maximize total boosted resource production with weights
    tot_sum = []
    # weights = {'emeralds':0, "ore":6, "crops":15, "fish":12, "wood":4}
    weights = {'emeralds':0, "ore":1,  "crops":3, "fish":3, "wood":1}
    for res in resources:
        tot_sum.append(res_prod_sum[res]*weights[res] - res_cost_sum[res]*weights[res])
    objective = solver.Sum(tot_sum)

    print("starting optimisation")

    solver.Maximize(objective)

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("✅ Optimal solution found.")
        for res in resources:
            print(f"{res} prod: {res_prod_sum[res].solution_value()}, cost: {res_cost_sum[res].solution_value()}")
        for t in territories:
            # print(territories[t]['categories'])
            for u, upgrade in upgrades.items():
                c = territories[t]['categories'][u]['index']
                g = territories[t]['categories'][u]['group']
                sol = np.array([[x[u, c, g, r, e].solution_value() for e in range(nk[u][1])] for r in range(nk[u][0])])
                for i, ut in enumerate(upgrade["upgrades"]):
                    territories[t]['upgrades'][ut] = int(np.argwhere(sol == 1)[0][i])
                    # I should also do storage upgrades here
    else:
        print("❌ No optimal solution found.")
        print(status)

    return territories


# strorage upgrades:
# Res: 0:0, 400:1, 800:3, 2000:7, 5000:14, 16000:33, 48000:79
# Ems: 0:0, 200:1, 400:3, 1000:7, 2500:14, 8000:33, 24000:79
# HQ storage is 5000, 1500. Other is 3000, 300
storage_levels = [
    (1, 0),
    (2, 400),
    (4, 800),
    (8, 2000),
    (15, 5000),
    (34, 16000),
    (80, 48000),
]
def get_storage_cost(prod, upgrade, hq=False, level=0):
    em = False
    if upgrade == "Emeralds":
        em = True
    base = 300
    if em: base = 3000
    if hq: base = 1500
    if hq and em: base = 5000

    for multi, cost in storage_levels:
        if multi*base >= prod/60:
            storage_cost = max(0, (cost-storage_levels[level][1]))
            if em:
                return int(storage_cost/2)
            else:
                return int(storage_cost)
    return 0