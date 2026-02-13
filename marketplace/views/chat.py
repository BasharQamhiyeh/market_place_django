from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db.models import Q

from marketplace.models import Item, Conversation, Message, Request, Store
from marketplace.validators import validate_no_links_or_html


@login_required
def start_conversation(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    listing = item.listing

    seller = listing.user
    buyer = request.user

    # don't allow messaging yourself
    if seller == buyer:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "self_message"}, status=400)
        return redirect("item_detail", item_id=item_id)

    # ✅ defensive: ensure this is a listing conversation (store must be null)
    convo = Conversation.objects.filter(
        listing=listing,
        store__isnull=True,
        buyer=buyer,
        seller=seller
    ).first()

    if not convo:
        convo = Conversation.objects.create(listing=listing, buyer=buyer, seller=seller)

    # If not POST: just go to chat as before
    if request.method != "POST":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "conversation_id": convo.id})
        return redirect("chat_room", conversation_id=convo.id)

    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)

    try:
        validate_no_links_or_html(body)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "invalid"}, status=400)

    Message.objects.create(conversation=convo, sender=request.user, body=body)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})

    return redirect("chat_room", conversation_id=convo.id)


@login_required
def start_conversation_request(request, request_id):
    req = get_object_or_404(Request, id=request_id)
    listing = req.listing

    # in your logic:
    seller = request.user       # helper
    buyer = listing.user        # requester

    if seller == buyer:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "self_message"}, status=400)
        return redirect("request_detail", request_id=request_id)

    # ✅ defensive: ensure this is a listing conversation (store must be null)
    convo = Conversation.objects.filter(
        listing=listing,
        store__isnull=True,
        buyer=buyer,
        seller=seller
    ).first()

    if not convo:
        convo = Conversation.objects.create(listing=listing, buyer=buyer, seller=seller)

    if request.method != "POST":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "conversation_id": convo.id})
        return redirect("chat_room", conversation_id=convo.id)

    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)

    try:
        validate_no_links_or_html(body)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "invalid"}, status=400)

    Message.objects.create(conversation=convo, sender=request.user, body=body)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})

    return redirect("chat_room", conversation_id=convo.id)


# ✅ NEW: start conversation with a Store (no listing attached)
@login_required
def start_store_conversation(request, store_id):
    store = get_object_or_404(Store, id=store_id, is_active=True)

    seller = store.owner
    buyer = request.user

    # don't allow messaging yourself
    if seller == buyer:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "self_message"}, status=400)
        return redirect("store_profile", store_id=store_id)

    convo = Conversation.objects.filter(
        store=store,
        listing__isnull=True,
        buyer=buyer,
        seller=seller
    ).first()

    if not convo:
        convo = Conversation.objects.create(store=store, buyer=buyer, seller=seller)

    # If not POST: just go to chat
    if request.method != "POST":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "conversation_id": convo.id})
        return redirect("chat_room", conversation_id=convo.id)

    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)

    try:
        validate_no_links_or_html(body)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "invalid"}, status=400)

    Message.objects.create(conversation=convo, sender=request.user, body=body)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "conversation_id": convo.id})

    return redirect("chat_room", conversation_id=convo.id)


@login_required
def chat_room(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "store", "buyer", "seller"),
        id=conversation_id
    )

    # SECURITY: Ensure user is part of the conversation
    if request.user not in [conversation.buyer, conversation.seller]:
        return redirect("item_list")

    listing = conversation.listing
    store = conversation.store

    item = None
    request_obj = None

    # Only resolve item/request if conversation is listing-based
    if listing:
        item = getattr(listing, "item", None)
        request_obj = getattr(listing, "request", None)

    # Mark unread messages (from the other user) as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    # SEND MESSAGE
    if request.method == "POST":
        body = request.POST.get("body", "").strip()

        if body:
            try:
                validate_no_links_or_html(body)
            except ValidationError:
                messages.error(request, "Links or HTML are not allowed in messages.")
            else:
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    body=body,
                )
                return redirect("chat_room", conversation_id=conversation_id)

    messages_qs = conversation.messages.select_related("sender").order_by("created_at")

    return render(
        request,
        "chat_room.html",
        {
            "conversation": conversation,
            "messages": messages_qs,
            "listing": listing,
            "store": store,          # ✅ NEW
            "item": item,
            "request_obj": request_obj,
        },
    )


@login_required
def user_inbox(request):
    convos = (
        Conversation.objects
        .filter(Q(buyer=request.user) | Q(seller=request.user))
        .select_related("listing", "store", "buyer", "seller")
        .order_by("-created_at")
    )

    return render(request, "inbox.html", {"convos": convos})
