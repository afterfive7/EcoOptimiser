import requests
import json
from dateutil import parser
from datetime import datetime, timezone, timedelta
from collections import deque

resources = ["emeralds", "ore", "wood", "fish", "crops"]
with open('data/resource_upgrades.json') as f:
    upgrades = json.load(f)

def get_guild_territories(guild_prefix: str, hq: str, force_tres=None):
    url = 'https://api.wynncraft.com/v3/guild/list/territory'
    r = requests.get(url)
    data = r.json()

    territories = {}
    now = datetime.now(timezone.utc)
    for k, v in data.items():
        if v['guild']['prefix'] == guild_prefix or guild_prefix is None:
            aq_time = parser.parse(v['acquired'])
            age = now - aq_time
            territories[k] = {"treasury": get_treasury_level(age)}
            if force_tres is not None:
                territories[k] = {"treasury": force_tres}
            territories[k]['upgrades'] = {}

    return territories

def load_territories(territories, hq):
    with open('data/territories.json') as f:
        d = json.load(f)

    d = territory_connections(hq, d)

    for t in territories:
        if t not in d:
            raise Exception(f"Territory \"{t}\" not found")

        distance = d[t]['distance']
        level = territories[t]['treasury']

        territories[t]['distance'] = distance
        territories[t]['resources'] = d[t]['resources']
        territories[t]['treasury_bonus'] = calc_treasury(level, distance)
        territories[t]['production'] = calc_production(territories[t])

    return territories

def calc_production(territory):
    production = {}
    for res in resources:
        production[res] = territory['resources'][res]*(1+territory['treasury_bonus'])
        for upgrade in upgrades.values():
            if res in upgrade["bonus_resources"]:
                x = upgrade['bonus']
                for u in upgrade['upgrades']:
                    x = x[territory['upgrades'].get(u,0)]
                production[res] *= 1+x
        production[res] = round(production[res])
    return production


def territory_connections(hq: str, territories:dict):
    connections = {k: v['Trading Routes'] for k, v in territories.items()}
    distances = {hq: 0}
    queue = deque([hq])

    while queue:
        current = queue.popleft()
        for neighbor in connections.get(current, []):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)

    for k, v in territories.items():
        if k in distances:
            v["distance"] = distances[k]
        else:
            v["distance"] = 6

    return territories

levels = [
    (timedelta(days=12), 0.30),
    (timedelta(days=5),  0.25),
    (timedelta(days=1),  0.20),
    (timedelta(hours=1), 0.10),
]
def get_treasury_level(age):
    for threshold, level in levels:
        if age >= threshold:
            return level
    return 0.0

def calc_treasury(level, distance):
    distance = max(min(distance, 6), 2)
    return (1 - (distance-2)*0.15)*level
# treasury: 1h, 1d, 5d, 12d, levels: 0, 10%, 20%, 25%, 30%
# distance bonus: 10%, 10%, 10%, 8.5%, 7%, 5.5%, 4%

storage_multis = [1, 2, 4, 8, 15, 34, 80]
def calc_storage_level(prod, res, hq):
    em = False
    if res == "Emeralds":
        em = True
    base = 300
    if em: base = 3000
    if hq: base = 1500
    if hq and em: base = 5000

    for i, multi in enumerate(storage_multis):
        if multi*base >= prod/60:
            return i
    return 0

