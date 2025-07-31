from optimiser import optimiser, territories
import json
import operator

ops = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le
}
with open('data/presets.json') as f:
    presets = json.load(f)

def from_api(prefix, hq):
    terrs = territories.get_guild_territories(prefix, hq)
    terrs = territories.load_territories(terrs, hq)

    # Using presets to set territory defenses
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