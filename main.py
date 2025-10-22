from optimizer import main
from optimizer import optimizer2 as optimizer

# prefix = 'SEQ'; hq = 'Bloody Trail'
# prefix = None; hq = 'Cathedral Harbour'
# prefix = "ESI"; hq = 'Central Islands'
# prefix = "AVO"; hq = 'Mine Base Plains'
# prefix = "ANO"; hq = "Nodguj Nation"
prefix = "Nia"; hq = "Nomads' Refuge"


# Importance of each resource. Rounded to 0.01
optimizer.weights = {'emeralds':0.00, "ore":1.00,  "crops":1.00, "fish":1.00, "wood":1.00}

# Tradeoff between min(yields) and sum(yields): higher values take longer but lead to more balanced yields.
# Rounded to 0.01
optimizer.balance = 1.50

# extra resource production to reserve
x = 5000
optimizer.extra_surplus = {'emeralds':50000, "ore":x, "crops":x, "fish":x, "wood":x}

presets_file = 'data/presets.json'
force_tres = None # VLow:0; Low:0.1; Medium:0.2, High:0.25; VHigh:0.3; None:Use current treasury from API
optimizer.num_threads = 10

main.from_api(prefix, hq, presets_file=presets_file, force_tres=force_tres, optimizer=optimizer)
# main.from_api(prefix, hq)

# input_file = 'input.json'