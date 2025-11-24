# marketplace/moderation.py

from __future__ import annotations
from typing import Tuple, Optional
from openai import OpenAI
from django.conf import settings
import traceback


def moderate_item(item) -> Tuple[str, Optional[str]]:
    """
    Real moderation using OpenAI (text only).
    FIXED VERSION:
    - After Listing refactor, Item no longer has (title, description)
    - Now uses item.listing.title and item.listing.description
    """

    # Listing may not exist if something failed earlier
    listing = getattr(item, "listing", None)

    if listing:
        title = listing.title or ""
        description = listing.description or ""
    else:
        # fallback to avoid crashes
        title = ""
        description = ""

    text = f"{title}\n{description}"

    # Connect to OpenAI client
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        organization=settings.OPENAI_ORG_ID,
        project=settings.OPENAI_PROJECT_ID,
    )

    try:
        response = client.moderations.create(
            model="omni-moderation-latest",
            input=text,
        )

        result = response.results[0]
        flagged = result.flagged
        categories = result.categories

        if flagged:
            reason_list = [name for name, value in categories.items() if value]
            reason = "Inappropriate content detected: " + ", ".join(reason_list)
            return "reject", reason

        return "manual", None

    except Exception as e:
        print("🚨 Moderation error type:", type(e).__name__)
        print("🚨 Moderation error repr:", repr(e))
        traceback.print_exc()
        return "manual", None
