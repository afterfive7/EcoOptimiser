import requests
import json
from dateutil import parser
from datetime import datetime, timezone, timedelta
from collections import deque

resources = ["emeralds", "ore", "wood", "fish", "crops"]
with open('resource_upgrades.json') as f:
    upgrades = json.load(f)

def get_guild_territories(guild_prefix: str, hq: str):
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
            territories[k]['upgrades'] = {}

    return territories

def load_territories(territories, hq):
    with open('territories.json') as f:
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
        # if 'upgrades' in territory:
        #     for upgrade in upgrades.values():
        #         if res in upgrade["bonus_resources"]:
        #             for i, ut in enumerate(upgrade['upgrades']):
        #                 if ut in territory['upgrades']:
        #                     production[res] *= (1+upgrades[upgrade]['bonus'][level[0]][level[1]])
        #
        #     for upgrade, level in territory['upgrades'].items():
        #         if res in upgrades[upgrade]["bonus_resources"]:
        #             production[res] *= (1+upgrades[upgrade]['bonus'][level[0]][level[1]])
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
