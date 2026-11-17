"""Hand-checkable example: 5 items, 3 signals, weights 0.5 / 0.3 / 0.2.

Signal values (multiples of 0.1):
        s1   s2   s3
    A   0.8  0.2  0.5
    B   0.6  0.9  0.1
    C   0.4  0.5  0.9
    D   0.2  0.7  0.3
    E   1.0  0.1  0.2

Working, per item: score = 0.5*s1 + 0.3*s2 + 0.2*s3
    A: 0.5*0.8 + 0.3*0.2 + 0.2*0.5 = 0.40 + 0.06 + 0.10 = 0.56
    B: 0.5*0.6 + 0.3*0.9 + 0.2*0.1 = 0.30 + 0.27 + 0.02 = 0.59
    C: 0.5*0.4 + 0.3*0.5 + 0.2*0.9 = 0.20 + 0.15 + 0.18 = 0.53
    D: 0.5*0.2 + 0.3*0.7 + 0.2*0.3 = 0.10 + 0.21 + 0.06 = 0.37
    E: 0.5*1.0 + 0.3*0.1 + 0.2*0.2 = 0.50 + 0.03 + 0.04 = 0.57
Ranking: B (0.59), E (0.57), A (0.56), C (0.53), D (0.37)

Mean of s1 = (0.8 + 0.6 + 0.4 + 0.2 + 1.0) / 5 = 3.0 / 5 = 0.6
With s1 replaced by 0.6 for everyone, s1 contributes 0.5*0.6 = 0.30 to every item:
    A: 0.30 + 0.06 + 0.10 = 0.46
    B: 0.30 + 0.27 + 0.02 = 0.59
    C: 0.30 + 0.15 + 0.18 = 0.63
    D: 0.30 + 0.21 + 0.06 = 0.57
    E: 0.30 + 0.03 + 0.04 = 0.37
Ranking: C (0.63), B (0.59), D (0.57), A (0.46), E (0.37)
"""

WEIGHTS = {"s1": 0.5, "s2": 0.3, "s3": 0.2}

ITEMS = [
    {"id": "A", "title": "Item A", "signals": {"s1": 0.8, "s2": 0.2, "s3": 0.5}},
    {"id": "B", "title": "Item B", "signals": {"s1": 0.6, "s2": 0.9, "s3": 0.1}},
    {"id": "C", "title": "Item C", "signals": {"s1": 0.4, "s2": 0.5, "s3": 0.9}},
    {"id": "D", "title": "Item D", "signals": {"s1": 0.2, "s2": 0.7, "s3": 0.3}},
    {"id": "E", "title": "Item E", "signals": {"s1": 1.0, "s2": 0.1, "s3": 0.2}},
]

# Expected values from the working above (to be compared with YOUR paper calculation).
SCORES = {"A": 0.56, "B": 0.59, "C": 0.53, "D": 0.37, "E": 0.57}
ORDER = ["B", "E", "A", "C", "D"]
SCORES_S1_OFF = {"A": 0.46, "B": 0.59, "C": 0.63, "D": 0.57, "E": 0.37}
ORDER_S1_OFF = ["C", "B", "D", "A", "E"]
