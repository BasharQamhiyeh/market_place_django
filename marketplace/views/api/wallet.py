from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from marketplace.models import PointsTransaction


@login_required
def api_wallet_summary(request):
    user = request.user

    txs = (
        PointsTransaction.objects
        .filter(user=user)
        .only("kind", "delta", "reason", "meta", "created_at")
        .order_by("-created_at")[:150]
    )

    def to_ui(tx):
        if tx.kind == PointsTransaction.Kind.SPEND:
            ui_type = "use"
        elif tx.kind == PointsTransaction.Kind.EARN:
            ui_type = "reward"
        else:
            ui_type = "reward" if tx.delta > 0 else "use"

        meta = dict(tx.meta or {})

        if tx.reason == "featured_listing":
            stored_type = meta.get("listing_type", "ad")
            meta.setdefault("action", "highlight")
            meta.setdefault("targetType", "request" if stored_type == "request" else "ad")
            meta.setdefault("id", meta.get("listing_id"))
            meta.setdefault("days", meta.get("days"))

        if tx.reason == "republish_listing":
            stored_type = meta.get("listing_type", "ad")
            meta.setdefault("action", "republish")
            meta.setdefault("targetType", "request" if stored_type == "request" else "ad")
            meta.setdefault("id", meta.get("listing_id"))
            meta.setdefault("title", meta.get("listing_title"))

        if tx.reason in ("buy_points", "admin_points"):
            ui_type = "buy"

        text = ""
        if tx.reason == "featured_listing":
            text = "تمييز إعلان"
        elif tx.reason == "republish_listing":
            text = "إعادة نشر"
        elif tx.reason == "referral_reward":
            text = "مكافأة دعوة صديق"
        elif tx.reason == "buy_points":
            text = f"شراء نقاط — باقة {abs(int(tx.delta))} نقطة"
        elif tx.reason == "admin_points":
            text = f"نقاط من ادمن ركن — {abs(int(tx.delta))} نقطة"
        else:
            text = tx.reason or ""

        return {
            "type": ui_type,
            "text": text,
            "amount": int(tx.delta),
            "date": tx.created_at.date().isoformat(),
            "meta": meta,
        }

    return JsonResponse({
        "ok": True,
        "points_balance": int(user.points),
        "transactions": [to_ui(t) for t in txs],
    })


def about(request):
    return render(request, "static_pages/about.html")