from collections import deque
import re


def _category_descendant_ids(root):
    """Return [root.id] + all descendant category IDs (BFS)."""
    ids = []
    dq = deque([root])
    while dq:
        node = dq.popleft()
        ids.append(node.id)
        # requires Category(parent=..., related_name="subcategories")
        for child in node.subcategories.all():
            dq.append(child)
    return ids


def _digits_only(s: str) -> str:
    return re.sub(r"\D+", "", (s or ""))


def _phone_candidates(raw: str) -> list[str]:
    d = _digits_only(raw)
    c = set()

    if d.startswith("07") and len(d) == 10:
        local07 = d
        norm962 = "962" + d[1:]
        c.update({local07, norm962, "+" + norm962, "00" + norm962})
        c.add(local07.lstrip("0"))  # legacy: 767xxxxxx

    elif d.startswith("9627") and len(d) == 12:
        norm962 = d
        local07 = "0" + d[3:]
        c.update({local07, norm962, "+" + norm962, "00" + norm962})
        c.add(local07.lstrip("0"))

    elif d.startswith("009627") and len(d) == 14:
        norm962 = d[2:]
        local07 = "0" + norm962[3:]
        c.update({local07, norm962, "+" + norm962, "00" + norm962})
        c.add(local07.lstrip("0"))
    else:
        return []

    c.discard("")
    return list(c)


def _status_from_listing(listing):
    # You may already have better fields (is_approved, rejected_at, reject_reason, etc.)
    if getattr(listing, "is_approved", False):
        return "active"
    # if you have a reject reason / rejected flag, treat as rejected
    reject_reason = getattr(listing, "reject_reason", "") or ""
    if reject_reason.strip():
        return "rejected"
    return "pending"


def _fmt_date(dt):
    if not dt:
        return ""
    # mockup uses YYYY/MM/DD
    return dt.strftime("%Y/%m/%d")


def translate_condition(condition):
    """Translate condition_preference to Arabic"""
    conditions_map = {
        "any": " لا يهم جديد أو مستعمل",
        "new": "جديد",
        "used": "مستعمل",
    }
    return conditions_map.get(condition, condition or "—")


def normalize_optional_url(raw: str | None) -> str:
    """
    Optional URL normalizer:
    - None/"" -> ""
    - "www.site.com" / "site.com" -> "https://site.com"
    - "http://..." / "https://..." kept
    - trims spaces
    """
    v = (raw or "").strip()
    if not v:
        return ""

    # Already has scheme
    if v.lower().startswith(("http://", "https://")):
        return v

    # Add default scheme
    return "https://" + v


def _user_avatar_url(u):
    """
    Return user avatar URL if it exists.
    If user has no avatar → return empty string.
    Frontend will handle fallback safely.
    """
    for attr in ("photo", "avatar", "image", "profile_photo"):
        f = getattr(u, attr, None)
        try:
            if f and getattr(f, "url", None):
                return f.url
        except Exception:
            pass

    # ✅ no avatar → return empty string (NOT a static path)
    return ""


def _other_party(convo, me):
  return convo.seller if convo.buyer_id == me.user_id else convo.buyer


def _convo_type_and_title(convo):
  # store conversation
  if convo.store_id:
    return ("store", "تواصل عام مع المتجر")

  # listing conversation => item or request
  listing = convo.listing
  item = getattr(listing, "item", None) if listing else None
  req = getattr(listing, "request", None) if listing else None

  if item:
    return ("ad", getattr(item, "title", "") or getattr(listing, "title", "") or "")
  if req:
    return ("request", getattr(req, "title", "") or getattr(listing, "title", "") or "")
  return ("ad", getattr(listing, "title", "") or "")
