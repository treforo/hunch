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
