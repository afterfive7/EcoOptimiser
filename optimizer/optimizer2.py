from ortools.sat.python import cp_model
import json

resources = ['emeralds'] + ["ore", "wood", "fish", "crops"]

extra_surplus = {'emeralds':0, "ore":0, "crops":0, "fish":0, "wood":0}
weights = {'emeralds':0, "ore":1,  "crops":1, "fish":1, "wood":1}
num_threads = 6
balance = 15

def prod_hash(res, prods):
    return "".join([r[0] + str(p) for r, p in zip(res, prods)])

def optimize_upgrades(territories):
    model = cp_model.CpModel()

    with open('data/resource_upgrades.json') as f:
        upgrades = json.load(f)
    with open('data/upgrades.json') as f:
        upgrade_costs = json.load(f)

    # Create production groups
    groups = {}
    curr_idx = 0
    for t in territories:
        for u in upgrades:
            res = upgrades[u]["bonus_resources"]
            terr_prods = [territories[t]['production'][r] for r in res]
            group_hash = prod_hash(res, terr_prods) # + str(curr_idx)
            if group_hash not in groups:
                groups[group_hash] = {
                    'territories': [],
                    'prod': dict(zip(res, terr_prods)),
                    'id': curr_idx,
                    'type': u
                }
                curr_idx += 1
            groups[group_hash]['territories'].append(t)

    print(f"number of groups: {curr_idx}")


    # Define ILP
    prods = {res:[] for res in resources}
    base_prods = {res: 0 for res in resources}
    costs = {res:[] for res in resources}
    base_costs = {res: 0 for res in resources}

    x = {}

    for g in groups.values():
        g_type = g['type']
        N = len(g['territories'])

        # Add variables for production upgrades
        vars = []
        for r in range(len(upgrades[g_type]['costs'])):  # rate upgrade
            for e in range(len(upgrades[g_type]['costs'][0])):  # efficiency upgrade
                x_i = model.NewIntVar(0, N, f"x_{g},{r},{e}")
                x[g['id'], r, e] = x_i
                vars.append(x_i)
                p_max = 0
                for res in resources:
                    base = g['prod'].get(res, 0)
                    bonus = upgrades[g_type]['bonus'][r][e]
                    cost = upgrades[g_type]['costs'][r][e].get(res, 0)

                    prods[res].append(x_i * int(base * bonus))
                    costs[res].append(x_i * cost)

                    p_max = max(p_max, int(base * bonus + base))

                # Account for storage requirements for prods
                storage_cost = get_storage_cost(p_max, g_type)
                if storage_cost > 0:
                    if g_type == "Emeralds":
                        costs['wood'].append(x_i * storage_cost)
                    else:
                        costs['emeralds'].append(x_i * storage_cost)

        model.Add(sum(vars) == N)

        # Add base production
        for res in resources:
            base = g['prod'].get(res, 0)
            base_prods[res] += base * N


    # Add costs for additional upgrades
    for territory in territories.values():
        for u,v in territory['upgrades'].items():
            res = upgrade_costs[u]["resource"]
            cost = upgrade_costs[u]['costs'][v]
            base_costs[res] += cost


    prod_sum = {}
    cost_sum = {}
    yields = []
    for res in resources:
        prod_sum[res] = sum(prods[res]) + base_prods[res]
        cost_sum[res] = sum(costs[res]) + base_costs[res] + extra_surplus[res]

        model.Add(prod_sum[res] >= cost_sum[res])
        if res != 'emeralds':
            yields.append(prod_sum[res] - cost_sum[res])

    min_yield = model.NewIntVar(0, 2**20, "min_yield")
    # model.AddMinEquality(min_yield, yields)
    for y in yields:
        model.Add(min_yield <= y)

    objective = (min_yield * balance + 10 * sum(yields)) * 10000 + (prod_sum['emeralds'] - cost_sum['emeralds'])
    model.Maximize(objective)


    print("starting optimisation")
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = num_threads

    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        print("✅ Optimal solution found.")
        print(f"min var: {solver.value(min_yield)}")
        print(f"objective: {solver.value(objective)}")
        for res in resources:
            print(f"{res} prod: {solver.value(prod_sum[res])}, cost: {solver.value(cost_sum[res])}")

        for g in groups.values():
            g_type = g['type']
            terrs = iter(g['territories'])
            for r in range(len(upgrades[g_type]['costs'])):  # rate upgrade
                for e in range(len(upgrades[g_type]['costs'][0])):  # efficiency upgrade
                    x_i = x[g['id'], r, e]
                    for i in range(solver.value(x_i)):
                        t = territories[next(terrs)]
                        u_type = upgrades[g_type]["upgrades"]
                        t['upgrades'][u_type[0]] = r
                        t['upgrades'][u_type[1]] = e
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