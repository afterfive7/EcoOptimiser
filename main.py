from optimiser import main, optimiser

# prefix = 'SEQ'; hq = 'Bloody Trail'
# prefix = 'BFS'; hq = 'Azure Frontier'
# prefix = None; hq = 'Cathedral Harbour'
# prefix = "ESI"; hq = 'Central Islands'
prefix = "AVO"; hq = 'Mine Base Plains'

weights = {'emeralds':0, "ore":1,  "crops":3, "fish":3, "wood":1}
extra_surplus = {'emeralds':2000, "ore":25000, "crops":25000, "fish":25000, "wood":25000}
presets_file = 'data/presets.json'
input_file = 'input.json'

optimiser.extra_surplus = extra_surplus
optimiser.weights = weights

main.from_api(prefix, hq, presets_file)
# main.from_import(input_file)