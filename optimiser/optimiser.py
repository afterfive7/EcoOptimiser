from ortools.linear_solver import pywraplp
import numpy as np

resources = ['emeralds'] + ["ore", "crops", "fish", "wood"]

def optimise_upgrades(territories, upgrades):
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
    res_prod_sum = {}
    res_cost_sum = {}
    for res in resources:
        prod_sum = []
        cost_sum = [50000]
        if res == "emeralds": cost_sum = [75000]
        for t, territory in territories.items():
            p = territory['production'][res]
            prod_sum.append(p)
            for u, upgrade in upgrades.items():
                if res in upgrade["bonus_resources"]:
                    for r in range(nk[u][0]):
                        for e in range(nk[u][1]):
                            bonus = upgrade['bonus'][r][e]
                            prod_sum.append(int(p*bonus)*x[t, u, r, e])
                for r in range(nk[u][0]):
                    for e in range(nk[u][1]):
                        if res in upgrade['costs'][r][e]:
                            cost = upgrade['costs'][r][e][res]
                            cost_sum.append(cost*x[t, u, r, e])

        res_prod_sum[res] = solver.Sum(prod_sum)
        res_cost_sum[res] = solver.Sum(cost_sum)
        solver.Add(res_prod_sum[res] >= res_cost_sum[res])
        # solver.Add(res_prod_sum[res] <= solver.Sum([res_cost_sum[res], 70000]))



    # Objective: maximize total boosted resource production
    tot_sum = []
    weights = {'emeralds':0, "ore":9, "crops":15, "fish":12, "wood":8}
    for res in resources:
        tot_sum.append(res_prod_sum[res]*weights[res] - res_cost_sum[res]*weights[res])
    objective = solver.Sum(tot_sum)

    solver.Maximize(objective)

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("✅ Optimal solution found.")
        # print(f"emeralds prod: {em_prod_sum.solution_value()}, cost: {em_cost_sum.solution_value()}")
        for res in resources:
            print(f"{res} prod: {res_prod_sum[res].solution_value()}, cost: {res_cost_sum[res].solution_value()}")
        for t, terr in territories.items():
            # print(t)
            terr['upgrades'] = {}
            for u in upgrades:
                sol = np.array([[x[t, u, r, e].solution_value() for e in range(nk[u][1])] for r in range(nk[u][0])])
                terr['upgrades'][u] = np.argwhere(sol == 1)[0]
                # print("   ", u, [x[t, u, l].solution_value() for l in range(nk[u])].index(1))
    else:
        print("❌ No optimal solution found.")

    return territories
