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


def from_api(prefix, hq, presets_file, force_tres=None):
    terrs = territories.get_guild_territories(prefix, hq, force_tres=force_tres)
    terrs = territories.load_territories(terrs, hq)

    with open(presets_file) as f:
        presets = json.load(f)
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

def from_import(import_file):
    with open(import_file) as f:
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
        prod = territories.calc_production(t)
        ishq = t['distance'] == 0
        t['production'] = prod
        t['upgrades']['resourceStorage'] = max(territories.calc_storage_level(max(list(prod.values())[1::]), 'Resources', ishq), t['upgrades'].get('resourceStorage', 0))
        t['upgrades']['emeraldStorage'] = max(territories.calc_storage_level(prod['emeralds'], 'Emeralds', ishq), t['upgrades'].get('emeraldStorage',0))


    result = {"hq": hq, "territories": {}, "tributes":{"emeralds":0,"ore":0,"wood":0,"fish":0,"crops":0}}

    for t, terr in terrs.items():
        result['territories'][t] = {
            "treasury": terr['treasury'],
            "upgrades": terr["upgrades"]
        }

    with open("output.json", "w") as f:
        json.dump(result, f, indent=4)