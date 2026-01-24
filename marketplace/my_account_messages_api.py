import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError

from marketplace.models import Conversation, Message
from marketplace.validators import validate_no_links_or_html  # adjust if path differs


def _conv_type_and_title(convo):
    # store conversation
    if convo.store_id and convo.listing_id is None:
        return "store", "تواصل عام مع المتجر"

    # listing conversation: could be item or request via reverse relations
    if convo.listing_id:
        listing = convo.listing
        # if your Listing has a related request (listing.request)
        if hasattr(listing, "request") and getattr(listing, "request", None):
            return "request", getattr(listing, "title", "") or ""
        return "ad", getattr(listing, "title", "") or ""

    return "ad", ""


@login_required
@require_GET
def my_account_conversations_api(request):
    convos = (
        Conversation.objects
        .filter(Q(buyer=request.user) | Q(seller=request.user))
        .select_related("listing", "store", "buyer", "seller")
        .order_by("-created_at")
    )

    out = []
    for c in convos:
        me_pk = request.user.pk
        other = c.seller if c.buyer_id == me_pk else c.buyer

        last = (
            Message.objects
            .filter(conversation=c)
            .order_by("-created_at")
            .only("body", "created_at")
            .first()
        )

        unread = (
            Message.objects
            .filter(conversation=c, is_read=False)
            .exclude(sender=request.user)
            .count()
        )

        ctype, title = _conv_type_and_title(c)

        out.append({
            "id": c.id,
            "name": getattr(other, "username", "مستخدم"),
            "img": "",  # put avatar URL if you have one
            "type": ctype,
            "title": title,
            "last": {
                "text": last.body if last else "لا توجد رسائل بعد",
                "time": timezone.localtime(last.created_at).strftime("%H:%M") if last else "",
            },
            "unreadCount": unread,
        })

    return JsonResponse({"ok": True, "conversations": out})


@login_required
@require_GET
def my_account_conversation_messages_api(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "store", "buyer", "seller"),
        id=conversation_id
    )

    if request.user not in [conversation.buyer, conversation.seller]:
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    # mark read (same as your chat_room)
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    me_pk = request.user.pk
    other = conversation.seller if conversation.buyer_id == me_pk else conversation.buyer

    ctype, title = _conv_type_and_title(conversation)

    type_text = (
        f"بخصوص إعلان: {title}" if ctype == "ad" else
        f"بخصوص طلب: {title}" if ctype == "request" else
        "محادثة عامة مع المتجر"
    )

    msgs = []
    qs = conversation.messages.select_related("sender").order_by("created_at")[:500]
    for m in qs:
        msgs.append({
            "id": m.id,
            "from": "me" if m.sender_id == request.user.pk else "them",
            "text": m.body,
            "time": timezone.localtime(m.created_at).strftime("%H:%M"),
        })

    return JsonResponse({
        "ok": True,
        "header": {
            "name": getattr(other, "username", "مستخدم"),
            "img": "",
            "typeText": type_text,
        },
        "messages": msgs,
    })


@login_required
@require_POST
def my_account_send_message_api(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    me_pk = request.user.pk
    if me_pk not in [conversation.buyer_id, conversation.seller_id]:
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    body = (payload.get("text") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)

    try:
        validate_no_links_or_html(body)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "invalid"}, status=400)

    m = Message.objects.create(conversation=conversation, sender=request.user, body=body)

    return JsonResponse({
        "ok": True,
        "message": {
            "id": m.id,
            "from": "me",
            "text": m.body,
            "time": timezone.localtime(m.created_at).strftime("%H:%M"),
        }
    })
