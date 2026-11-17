"""Named constants for Hunch (Stage 1). tau1, tau2 and the seed are added in later stages."""

# The five invented signals, in a fixed order. They are NOT Facebook's.
SIGNALS = ["topic_affinity", "followed_account", "popularity", "recency", "similar_users"]

# Invented weights: personal signals outweigh crowd signals. They sum to 1.00.
WEIGHTS = {
    "topic_affinity": 0.35,
    "followed_account": 0.25,
    "popularity": 0.15,
    "recency": 0.15,
    "similar_users": 0.10,
}

N_ITEMS = 40     # items ranked
FEED_SIZE = 10   # the feed shows the top 10; rank 11 or worse is "out of the feed"

# Stage 2: verdict thresholds (places the item falls in the ranking when the guessed signal is off)
TAU1 = 5  # fall of at least this many places (or dropping out of the feed) = Supported
TAU2 = 2  # fall of at least this many but less than TAU1 = Partly supported

# Verdict labels, in words so the UI never relies on colour alone
SUPPORTED = "Supported"
PARTLY_SUPPORTED = "Partly supported"
NOT_SUPPORTED = "Not supported"
NOT_USED = "Not used"

OTHER_GUESS = "other"  # a guess that maps to none of the five signals, e.g. "a friend shared it"
