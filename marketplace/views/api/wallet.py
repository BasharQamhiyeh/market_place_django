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
            meta.setdefault("action", "highlight")
            meta.setdefault("targetType", "ad")
            meta.setdefault("id", meta.get("listing_id"))
            meta.setdefault("days", meta.get("days"))

        if tx.reason == "buy_points":
            ui_type = "buy"

        text = ""
        if tx.reason == "featured_listing":
            text = "تمييز إعلان"
        elif tx.reason == "referral_reward":
            text = "مكافأة دعوة صديق"
        elif tx.reason == "buy_points":
            text = f"شراء نقاط — باقة {abs(int(tx.delta))} نقطة"
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