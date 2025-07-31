from optimiser import optimiser, territories
import json
import operator
import copy

# prefix = 'SEQ'; hq = 'Bloody Trail'
# prefix = 'BFS'; hq = 'Azure Frontier'
# prefix = None; hq = 'Cathedral Harbour'
prefix = "ESI"; hq = 'Central Islands'



ops = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le
}
with open('presets.json') as f:
    presets = json.load(f)

def from_api(prefix, hq):
    terrs = territories.get_guild_territories(prefix, hq)
    terrs = territories.load_territories(terrs, hq)

    for t in terrs.values():
        for preset in presets.values():
            if preset["condition"] == {}:
                t["upgrades"] = preset["upgrades"].copy()
                break
            field = t
            for v in preset["condition"]["variable"]:
                field = field[v]
            op = preset["condition"]["op"]
            value = preset["condition"]["value"]
            if ops[op](field, value):
                t["upgrades"] = preset["upgrades"].copy()
                break
    main(terrs, hq)

def from_import(file):
    with open(file) as f:
        data = json.load(f)
    terrs = data["territories"]
    hq = data["hq"]
    # Reset production because we are optimizing these duh...
    for t in terrs.values():
        for u in t["upgrades"]:
            if u in ["emeraldRate", "efficientEmeralds", "resourceRate", "efficientResources"]:
                t["upgrades"][u] = 0
    terrs = territories.load_territories(terrs, hq)
    main(terrs, hq)

def main(terrs, hq):
    terrs = optimiser.optimise_upgrades(terrs)

    for t in terrs.values():
        t['production'] = territories.calc_production(t)


    result = {"hq": hq, "territories": {}}

    for t, terr in terrs.items():
        result['territories'][t] = {
            "treasury": terr['treasury'],
            "upgrades": terr["upgrades"]
        }

    with open("output.json", "w") as f:
        json.dump(result, f, indent=4)


# from_api(prefix, hq)
from_import("output.json")


# for res in ["emeralds", "ore", "crops", "fish", "wood"]:
#     sum = 0
#     for terr in terrs.values():
#         sum += int(terr['production'][res])
#     print(f"{res}: {sum}")
#
# for t, terr in terrs.items():
#     print(terr['production']['emeralds'])