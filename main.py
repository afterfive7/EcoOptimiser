from optimizer import main
from optimizer import optimizer2 as optimizer

# prefix = 'SEQ'; hq = 'Bloody Trail'
# prefix = None; hq = 'Cathedral Harbour'
# prefix = "ESI"; hq = 'Central Islands'
# prefix = "AVO"; hq = 'Mine Base Plains'
# prefix = "ANO"; hq = "Nodguj Nation"
prefix = "Nia"; hq = "Nomads' Refuge"

weights = {'emeralds':0, "ore":1,  "crops":1, "fish":1.2, "wood":1}
x = 5000
extra_surplus = {'emeralds':50000, "ore":x, "crops":x, "fish":x, "wood":x}
presets_file = 'data/presets.json'
force_tres = None # VLow:0; Low:0.1; Medium:0.2, High:0.25; VHigh:0.3; None:Use current treasury from API
num_threads = 10

optimizer.extra_surplus = extra_surplus
optimizer.weights = weights
optimizer.num_threads = num_threads
optimizer.balance = 1.5 # tradeoff between min(yields) and sum(yields), higher values take longer but lead to more balanced yields. rounded to .1

main.from_api(prefix, hq, presets_file=presets_file, force_tres=force_tres, optimizer=optimizer)
# main.from_api(prefix, hq)

# input_file = 'input.json'