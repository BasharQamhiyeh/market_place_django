import json

from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Q, Count, Subquery
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from marketplace.models import Message, Conversation
from marketplace.validators import validate_no_links_or_html
from marketplace.views.helpers import _other_party, _convo_type_and_title, _user_avatar_url


@login_required
@require_GET
def api_my_conversations(request):
  me = request.user

  last_msg_qs = (
    Message.objects
    .filter(conversation_id=OuterRef("pk"))
    .order_by("-created_at")
  )

  qs = (
    Conversation.objects
    .filter(Q(buyer=me) | Q(seller=me))
    .select_related("buyer", "seller", "listing", "store")
    .annotate(
      last_body=Subquery(last_msg_qs.values("body")[:1]),
      last_time=Subquery(last_msg_qs.values("created_at")[:1]),
      unread_count=Count(
        "messages",
        filter=Q(messages__is_read=False) & ~Q(messages__sender=me),
        distinct=True
      ),
    )
    .order_by("-last_time", "-created_at")
  )

  out = []
  for c in qs:
    other = _other_party(c, me)
    ctype, title = _convo_type_and_title(c)

    # display name
    if c.store_id and getattr(c.store, "name", None):
      name = c.store.name
      img = getattr(getattr(c.store, "logo", None), "url", None) or _user_avatar_url(other)
    else:
      name = getattr(other, "username", None) or (f"{other.first_name} {other.last_name}".strip() or "مستخدم")
      img = _user_avatar_url(other)

    last_time = c.last_time
    last_time_str = timezone.localtime(last_time).strftime("%I:%M %p") if last_time else ""

    out.append({
      "id": c.id,
      "name": name,
      "type": ctype,
      "title": title,
      "img": img,
      "unreadCount": int(c.unread_count or 0),
      "lastText": c.last_body or "لا توجد رسائل بعد",
      "lastTime": last_time_str,
    })

  return JsonResponse({"conversations": out})


@login_required
@require_GET
def api_conversation_messages(request, conversation_id):
  me = request.user

  convo = (
    Conversation.objects
    .select_related("buyer", "seller", "store", "listing")
    .get(id=conversation_id)
  )
  if me not in [convo.buyer, convo.seller]:
    return JsonResponse({"messages": []}, status=403)

  other = _other_party(convo, me)

  # mark unread as read
  Message.objects.filter(conversation=convo, is_read=False).exclude(sender=me).update(is_read=True)

  msgs = (
    convo.messages
    .select_related("sender")
    .order_by("created_at")
  )

  other_avatar = _user_avatar_url(other)
  data = []
  for m in msgs:
    data.append({
      "from": "me" if m.sender_id == me.pk else "them",
      "text": m.body,
      "time": timezone.localtime(m.created_at).strftime("%I:%M %p"),
      "avatar": other_avatar,
    })

  return JsonResponse({"messages": data})


@login_required
@require_POST
def api_conversation_send(request, conversation_id):
  me = request.user

  convo = (
    Conversation.objects
    .select_related("buyer", "seller")
    .get(id=conversation_id)
  )
  if me.pk not in [convo.buyer_id, convo.seller_id]:
      return JsonResponse({"messages": []}, status=403)

  try:
    payload = json.loads(request.body.decode("utf-8"))
  except Exception:
    payload = {}

  body = (payload.get("body") or "").strip()
  if not body:
    return JsonResponse({"ok": False, "error": "empty"}, status=400)

  # keep your validation
  from django.core.exceptions import ValidationError
  try:
    validate_no_links_or_html(body)
  except ValidationError:
    return JsonResponse({"ok": False, "error": "invalid"}, status=400)

  Message.objects.create(conversation=convo, sender=me, body=body)
  return JsonResponse({"ok": True})