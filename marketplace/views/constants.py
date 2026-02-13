from market_place import settings

IS_RENDER = getattr(settings, "IS_RENDER", False)
ALLOWED_PAYMENT_METHODS = {"cash", "card", "cliq", "transfer"}
ALLOWED_DELIVERY = {"24", "48", "72"}
ALLOWED_RETURN = {"3", "7", "none"}

REFERRAL_POINTS = 50

FEATURE_PACKAGES = {3: 30, 7: 60, 14: 100}


try:
    from django.contrib.postgres.search import TrigramSimilarity
    TRIGRAM_AVAILABLE = True
except Exception:
    TRIGRAM_AVAILABLE = False