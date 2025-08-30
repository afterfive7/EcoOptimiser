from optimiser import main, optimiser

# prefix = 'SEQ'; hq = 'Bloody Trail'
# prefix = None; hq = 'Cathedral Harbour'
# prefix = "ESI"; hq = 'Central Islands'
prefix = "AVO"; hq = 'Mine Base Plains'

weights = {'emeralds':0, "ore":1,  "crops":1, "fish":1, "wood":1}
x = 5000
extra_surplus = {'emeralds':2000, "ore":x, "crops":x, "fish":x, "wood":x}
presets_file = 'data/presets.json'
force_tres = None # VLow:0; Low:0.1; Medium:0.2, High:0.25; VHigh:0.3; None:Use current treasury from API
num_threads = 1

optimiser.extra_surplus = extra_surplus
optimiser.weights = weights
optimiser.num_threads = num_threads

main.from_api(prefix, hq, presets_file=presets_file, force_tres=force_tres)
# main.from_api(prefix, hq)

# input_file = 'input.json'
# main.from_import(input_file)