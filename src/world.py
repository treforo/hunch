"""Seeded world: 40 items, one user profile, hand-planted causes.

Everything here is SIMULATED. The signals, weights and planted causes are invented.

Design in one paragraph. 10 items are planted. Each single-cause item has ONE signal
set high and its other four signals set exactly equal to the feed-wide mean, so
switching a non-cause signal off cannot change that item's score. The remaining 30
items are background: 22 random items kept below the average score, plus 8 "filler"
items whose scores sit just above the average. The fillers are what an item falls
behind when it loses everything (see the redundant pair below).

The EXPECTED verdicts in PLANTED_DESIGN are written by hand from this design. They are
never computed by the tester or the verdict engine.
"""

import random

from src.config import (WEIGHTS, N_ITEMS, FEED_SIZE, SEED, SUPPORTED, NOT_SUPPORTED,
                        NOT_USED, OTHER_GUESS)
from src.ranker import validate_items, signal_mean, rank

# ---- design constants (world construction only; not the verdict thresholds) ----
N_FILLERS = 8
N_RANDOM_BG = N_ITEMS - 10 - N_FILLERS   # 22 random background items
BG_LOW, BG_HIGH = 0.05, 0.45             # range of each random background signal
BG_CAP = 0.30                            # a random background item must score at most this
FILLER_MIN, FILLER_MAX = 0.005, 0.030    # fillers score this far ABOVE the average score
FILLER_SPREAD = 0.05                     # how much a filler's signals differ from each other
CAUSE_VALUE = 1.0                        # value of a single cause signal
PAIR_VALUE = 0.65                        # value of each signal of the redundant pair
SOCIAL_OFFSET = 0.09                     # the social item sits this far above the mean on EVERY signal

# Descriptive only: the profile labels the world and plays no part in ranking.
USER_PROFILE = {"name": "Sam", "interests": ["cooking", "cycling"],
                "followed_accounts": ["@bakery", "@cycleclub"]}

SOCIAL_CAUSE = "social (a friend shared it)"

# Hand-written design table. For each planted item:
#   key, role, cause signals, correct guess + expected verdict, adjacent wrong guess + expected verdict
# Reasoning for the expected verdicts:
#   single, correct guess : with its cause switched off the item scores the all-average level, which
#                           is below the 8 other planted items and the 8 fillers -> it drops out.
#   single, wrong guess   : its other four signals already equal the mean, so switching one off leaves
#                           its score unchanged, and items above it can only fall -> fall of 0 or less.
#   social, "other"       : the guess maps to no signal -> Not used.
#   social, wrong guess   : every signal is only slightly above the mean, so no single signal
#                           moves it by 2 places.
#   redundant pair        : both signals are real causes, so each guess is true -> Supported. That is the
#                           ground truth the single-signal test is compared with.
PLANTED_DESIGN = [
    {"key": "T1", "role": "single", "causes": ["topic_affinity"],
     "correct": ("topic_affinity", SUPPORTED), "wrong": ("followed_account", NOT_SUPPORTED)},
    {"key": "T2", "role": "single", "causes": ["topic_affinity"],
     "correct": ("topic_affinity", SUPPORTED), "wrong": ("followed_account", NOT_SUPPORTED)},
    {"key": "F1", "role": "single", "causes": ["followed_account"],
     "correct": ("followed_account", SUPPORTED), "wrong": ("topic_affinity", NOT_SUPPORTED)},
    {"key": "F2", "role": "single", "causes": ["followed_account"],
     "correct": ("followed_account", SUPPORTED), "wrong": ("topic_affinity", NOT_SUPPORTED)},
    {"key": "P1", "role": "single", "causes": ["popularity"],
     "correct": ("popularity", SUPPORTED), "wrong": ("similar_users", NOT_SUPPORTED)},
    {"key": "P2", "role": "single", "causes": ["popularity"],
     "correct": ("popularity", SUPPORTED), "wrong": ("similar_users", NOT_SUPPORTED)},
    {"key": "R1", "role": "single", "causes": ["recency"],
     "correct": ("recency", SUPPORTED), "wrong": ("popularity", NOT_SUPPORTED)},
    {"key": "S1", "role": "single", "causes": ["similar_users"],
     "correct": ("similar_users", SUPPORTED), "wrong": ("popularity", NOT_SUPPORTED)},
    {"key": "SOC", "role": "social", "causes": [],
     "correct": (OTHER_GUESS, NOT_USED), "wrong": ("followed_account", NOT_SUPPORTED)},
    {"key": "RP", "role": "redundant_pair", "causes": ["popularity", "similar_users"],
     "pair_truth": {"popularity": SUPPORTED, "similar_users": SUPPORTED}},
]


def generate_world(seed=SEED):
    """Build the world from a seed. Returns
    {"items", "weights", "user", "means", "seed"}.
    Raises ValueError if a design precondition fails (see check_design).
    """
    rng = random.Random(seed)   # a private generator, so nothing else can change the world
    signals = list(WEIGHTS)

    # 1. Random background items, each kept only if it scores at most BG_CAP.
    background = []
    while len(background) < N_RANDOM_BG:
        values = {s: rng.uniform(BG_LOW, BG_HIGH) for s in signals}
        if sum(WEIGHTS[s] * values[s] for s in signals) <= BG_CAP:
            background.append(values)

    # 2. Fillers: offsets from the mean. Offset t_i is the filler's score above the average score;
    #    random per-signal differences are shifted so the weighted sum of the offsets is exactly t_i.
    fillers = []
    for i in range(N_FILLERS):
        t = FILLER_MIN + i * (FILLER_MAX - FILLER_MIN) / (N_FILLERS - 1)
        u = {s: rng.uniform(-FILLER_SPREAD, FILLER_SPREAD) for s in signals}
        shift = sum(WEIGHTS[s] * u[s] for s in signals)   # weights sum to 1, so this is exact
        fillers.append({s: t + u[s] - shift for s in signals})

    # 3. Planted items: fixed cause values, and offsets for the slots that take the mean.
    planted = []
    for spec in PLANTED_DESIGN:
        if spec["role"] == "redundant_pair":
            cause_values = {s: PAIR_VALUE for s in spec["causes"]}
        else:
            cause_values = {s: CAUSE_VALUE for s in spec["causes"]}
        offset = SOCIAL_OFFSET if spec["role"] == "social" else 0.0
        planted.append((spec, cause_values, offset))

    # 4. The feed-wide mean mu_s includes the planted items, whose non-cause values equal mu_s.
    #    So mu_s is the solution of one linear equation per signal:
    #       mu_s * (N - m_s) = (fixed values) + (offsets),  m_s = items whose slot takes the mean.
    means = {}
    for s in signals:
        fixed = sum(v[s] for v in background)
        fixed += sum(cv[s] for _, cv, _ in planted if s in cv)
        offsets = sum(off for _, cv, off in planted if s not in cv)
        offsets += sum(f[s] for f in fillers)
        takes_mean = sum(1 for _, cv, _ in planted if s not in cv) + N_FILLERS
        means[s] = (fixed + offsets) / (N_ITEMS - takes_mean)

    # 5. Build all 40 items, then shuffle so planted items do not have consecutive ids.
    slots = []
    for spec, cause_values, offset in planted:
        values = {s: cause_values[s] if s in cause_values else means[s] + offset for s in signals}
        slots.append({"signals": values, "design_role": spec["role"], "spec": spec})
    for f in fillers:
        slots.append({"signals": {s: means[s] + f[s] for s in signals}, "design_role": "filler"})
    for v in background:
        slots.append({"signals": v, "design_role": "background"})
    rng.shuffle(slots)

    items = []
    for number, slot in enumerate(slots, start=1):
        item = {"id": number, "title": f"Post {number}", "signals": slot["signals"],
                "design_role": slot["design_role"]}
        spec = slot.get("spec")
        if spec:
            item["planted_key"] = spec["key"]
            item["planted_cause"] = (SOCIAL_CAUSE if spec["role"] == "social"
                                     else "+".join(spec["causes"]))
            if spec["role"] == "redundant_pair":
                item["expected"] = {"pair_truth": spec["pair_truth"]}
            else:
                item["expected"] = {"correct": spec["correct"], "wrong": spec["wrong"]}
        items.append(item)

    world = {"items": items, "weights": dict(WEIGHTS), "user": USER_PROFILE,
             "means": means, "seed": seed}
    check_design(world)
    return world


def check_design(world, tolerance=1e-9):
    """Check the construction did what the design says. These are properties of the DATA only:
    nothing here calls the tester or the verdict engine. Raises ValueError on the first failure.
    """
    items, weights = world["items"], world["weights"]
    validate_items(items, weights)
    if len(items) != N_ITEMS:
        raise ValueError(f"Expected {N_ITEMS} items, found {len(items)}")

    means = {s: signal_mean(items, s) for s in weights}
    base = sum(weights[s] * means[s] for s in weights)   # the all-average score

    def score(item):
        return sum(weights[s] * item["signals"][s] for s in weights)

    planted = [i for i in items if "planted_key" in i]
    if len(planted) != 10:
        raise ValueError(f"Expected 10 planted items, found {len(planted)}")

    # Single-cause items: cause high, every other signal equal to the feed-wide mean.
    for item in planted:
        if item["design_role"] != "single":
            continue
        cause = item["planted_cause"]
        if item["signals"][cause] != CAUSE_VALUE:
            raise ValueError(f"Item {item['id']}: cause {cause} is not {CAUSE_VALUE}")
        for s in weights:
            if s != cause and abs(item["signals"][s] - means[s]) > tolerance:
                raise ValueError(f"Item {item['id']}: {s} is not equal to the mean")

    # Social item: every signal above the mean by the same small offset (none dominant).
    for item in planted:
        if item["design_role"] == "social":
            for s in weights:
                if abs(item["signals"][s] - means[s] - SOCIAL_OFFSET) > tolerance:
                    raise ValueError(f"Social item {item['id']}: {s} is not mean + offset")

    # Redundant pair: both pair signals high, the other three equal to the mean.
    pair = [i for i in planted if i["design_role"] == "redundant_pair"]
    if len(pair) != 1:
        raise ValueError("Expected exactly one redundant pair item")
    rp = pair[0]
    pair_signals = rp["planted_cause"].split("+")
    for s in weights:
        want = PAIR_VALUE if s in pair_signals else means[s]
        if abs(rp["signals"][s] - want) > tolerance:
            raise ValueError(f"Pair item {rp['id']}: {s} is not {want}")

    # Fillers score just above the all-average score; random background scores below it.
    fillers = [i for i in items if i["design_role"] == "filler"]
    random_bg = [i for i in items if i["design_role"] == "background"]
    if len(fillers) != N_FILLERS or len(random_bg) != N_RANDOM_BG:
        raise ValueError("Wrong number of filler or background items")
    for item in fillers:
        if not base < score(item) <= base + FILLER_MAX + tolerance:
            raise ValueError(f"Filler {item['id']} is not just above the average score")
    for item in random_bg:
        if score(item) >= base:
            raise ValueError(f"Background item {item['id']} scores at or above the average score")

    # Fillers must sit below where the pair item lands when ONE of its signals is switched off,
    # so a single removal does not pass them; only removing both does.
    for s in pair_signals:
        left = sum(weights[o] * (rp["signals"][o] - means[o]) for o in pair_signals if o != s)
        if FILLER_MAX >= left:
            raise ValueError(f"Fillers reach the pair item's level with {s} removed")

    # All 10 planted items must be in the feed, so guesses can be offered for each.
    top = {row["id"] for row in rank(items, weights) if row["rank"] <= FEED_SIZE}
    if top != {i["id"] for i in planted}:
        raise ValueError("The 10 planted items are not exactly the top 10")
