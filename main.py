from optimiser import main

# prefix = 'SEQ'; hq = 'Bloody Trail'
# prefix = 'BFS'; hq = 'Azure Frontier'
# prefix = None; hq = 'Cathedral Harbour'
# prefix = "ESI"; hq = 'Central Islands'
prefix = "AVO"; hq = 'Mine Base Plains'



main.from_api(prefix, hq)
# main.from_import("input.json")