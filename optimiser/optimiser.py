from ortools.linear_solver import pywraplp
import numpy as np
import json

resources = ['emeralds'] + ["ore", "wood", "fish", "crops"]

with open('data/resource_upgrades.json') as f:
    upgrades = json.load(f)
with open('data/upgrades.json') as f:
    upgrade_costs = json.load(f)

def optimise_upgrades(territories):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    solver.SetNumThreads(6)
    if not solver:
        raise RuntimeError("Solver not created.")

    # Decision variables: x[t][u][r][e] = 1 if territory i gets upgrade u with rate r and efficiency e
    x = {}
    nk = {k: (len(v['costs']), len(v['costs'][0])) for k, v in upgrades.items()}

    for t in territories:
        for u in upgrades:
            for r in range(nk[u][0]):  # rate
                for e in range(nk[u][1]):  # efficiency
                    x[t, u, r, e] = solver.IntVar(0, 1, f"x_{t}_{u}_{r}_{e}")

    # Constraint: only one upgrade per territory
    for t in territories:
        for u in upgrades:
            solver.Add(solver.Sum(x[t, u, r, e] for r in range(nk[u][0]) for e in range(nk[u][1])) == 1)

    # Constraint: total emerald cost must be within budget
    # each resource cost < prod
    # add defense costs etc later
    res_prod = {res:[] for res in resources}
    res_cost = {res:[] for res in resources}
    terr_cost = {}
    for t, territory in territories.items():
        terr_cost[t]= {res:[] for res in resources}
        for res in resources:
            p = territory['production'][res]
            if p > 0:
                res_prod[res].append(p)
            for u, upgrade in upgrades.items():
                for r in range(nk[u][0]):
                    for e in range(nk[u][1]):
                        if res in upgrade["bonus_resources"]: # Upgrade bonusses
                            bonus = int(p*upgrade['bonus'][r][e])
                            if bonus > 0:
                                res_prod[res].append(bonus*x[t, u, r, e])
                        if res in upgrade['costs'][r][e]: # Upgrade costs
                            cost = upgrade['costs'][r][e][res]
                            if cost > 0:
                                res_cost[res].append(cost*x[t, u, r, e])
                                terr_cost[t][res].append(cost*x[t, u, r, e])

        # Calculate cost caused by storage requirements
        pem = territory['production']['emeralds']
        pmax = max(territory['production'][res] for res in resources[1::])

        for r in range(nk['Emeralds'][0]):
            for e in range(nk['Emeralds'][1]):
                bonus = int(pem*upgrades['Emeralds']['bonus'][r][e])
                # ignore additional storage requirement from emerald usage. This seems to complex
                level = territory["upgrades"].get("emeraldStorage",0)
                storage_cost = get_storage_cost(pem + bonus, em=True, hq=(territory['distance']==0), level=level)
                if storage_cost > 0:
                    res_cost['wood'].append(storage_cost*x[t, 'Emeralds', r, e])
                    terr_cost[t]['wood'].append(storage_cost*x[t, 'Emeralds', r, e])

        for r in range(nk['Resources'][0]):
            for e in range(nk['Resources'][1]):
                bonus = int(pmax*upgrades['Resources']['bonus'][r][e])
                level = territory["upgrades"].get("resourceStorage",0)
                storage_cost = get_storage_cost(pmax + bonus, hq=(territory['distance']==0), level=level)
                if storage_cost > 0:
                    res_cost['emeralds'].append(storage_cost*x[t, 'Resources', r, e])
                    terr_cost[t]['emeralds'].append(storage_cost*x[t, 'Resources', r, e])

        # Add costs for additional upgrades
        for u,v in territory['upgrades'].items():
            res = upgrade_costs[u]["resource"]
            cost = upgrade_costs[u]['costs'][v]
            res_cost[res].append(cost)
            terr_cost[t][res].append(cost)

    res_prod_sum = {}
    res_cost_sum = {}
    extra_surpluss = {'emeralds':0, "ore":0, "crops":0, "fish":0, "wood":0}
    for res in resources:
        res_prod_sum[res] = solver.Sum(res_prod[res])
        res_cost_sum[res] = solver.Sum(res_cost[res])
        solver.Add(res_prod_sum[res] >= res_cost_sum[res] + extra_surpluss[res])
        # solver.Add(res_prod_sum[res] <= solver.Sum([res_cost_sum[res], 100000]))


    # Objective: maximize total boosted resource production with weights
    tot_sum = []
    weights = {'emeralds':0, "ore":6, "crops":15, "fish":12, "wood":4}
    for res in resources:
        tot_sum.append(res_prod_sum[res]*weights[res] - res_cost_sum[res]*weights[res])
    objective = solver.Sum(tot_sum)

    print("starting optimization")

    solver.Maximize(objective)

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("✅ Optimal solution found.")
        for res in resources:
            print(f"{res} prod: {res_prod_sum[res].solution_value()}, cost: {res_cost_sum[res].solution_value()}")
        for t in territories:
            for u, upgrade in upgrades.items():
                sol = np.array([[x[t, u, r, e].solution_value() for e in range(nk[u][1])] for r in range(nk[u][0])])
                for i, ut in enumerate(upgrade["upgrades"]):
                    territories[t]['upgrades'][ut] = int(np.argwhere(sol == 1)[0][i])
    else:
        print("❌ No optimal solution found.")

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
def get_storage_cost(prod, em=False, hq=False, level=0):
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