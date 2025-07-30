from datetime import timedelta

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

def calc_treasury(age, distance):
    distance = max(min(distance, 6), 2)
    level =get_treasury_level(age)
    return (10 - (distance-2)*1.5)*level
# treasury: 1h, 1d, 5d, 12d, levels: 0, 1, 2, 2.5, 3
# distance bonus: 10, 10, 10, 8.5, 7, 5.5, 4

class Territory:
    def __init__(self, name: str, resources: list[int], age, distance):
        self.name = name
        self.resources = resources
        self.treasury = calc_treasury(age, distance)

    def bonus(self, name: str, level: int):
