# marketplace/moderation.py

from __future__ import annotations

import logging
import traceback
from typing import Optional, Tuple

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


def moderate_item(item) -> Tuple[str, Optional[str]]:
    """
    Moderate a newly created Item using the OpenAI Moderation API.

    Returns a (decision, reason) tuple where decision is one of:
    - "approve": content is clean — set is_approved=True
    - "reject":  content flagged — auto-reject the listing
    - "manual":  API unavailable or inconclusive — queue for human review
    """
    listing = getattr(item, "listing", None)
    title = listing.title if listing else ""
    description = listing.description if listing else ""
    text = f"{title}\n{description}".strip()

    if not settings.OPENAI_API_KEY:
        logger.info(
            "OPENAI_API_KEY is not configured. Item %s queued for manual review.", item.id
        )
        return "manual", None

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
        if result.flagged:
            reason_list = [name for name, value in result.categories if value]
            reason = "Inappropriate content detected: " + ", ".join(reason_list)
            logger.info("Item %s auto-rejected: %s", item.id, reason)
            return "reject", reason

        return "approve", None

    except Exception:
        logger.error(
            "Moderation API error for item %s — falling back to manual review:\n%s",
            item.id,
            traceback.format_exc(),
        )
        return "manual", None
