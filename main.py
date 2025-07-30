from optimiser import optimiser, territories
import json

# prefix = 'SEQ'; hq = 'Bloody Trail'
# prefix = 'BFS'; hq = 'Azure Frontier'
# prefix = None; hq = 'Cathedral Harbour'
prefix = "ESI"; hq = 'Central Islands'
terrs = territories.get_guild_territories(prefix, hq)
with open('upgrades.json') as f:
    upgrades = json.load(f)
terrs = optimiser.optimise_upgrades(terrs, upgrades)

for t in terrs.values():
    t['production'] = territories.calc_production(t)

result = {"hq": hq, "territories": {}}

for t, terr in terrs.items():
    result['territories'][t] = {
        "treasury": terr['treasury'],
        "upgrades": {
            "efficientResources": int(terr['upgrades']['Resources'][1]),
            "efficientEmeralds": int(terr['upgrades']['Emeralds'][1]),
            "resourceRate": int(terr['upgrades']['Resources'][0]),
            "emeraldRate": int(terr['upgrades']['Emeralds'][0])
        }
    }

with open("output.json", "w") as f:
    json.dump(result, f, indent=4)


print()
# for res in ["emeralds", "ore", "crops", "fish", "wood"]:
#     sum = 0
#     for terr in terrs.values():
#         sum += terr['production'][res]
#     print(f"{res}: {sum}")