# marketplace/api_views.py
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Q, Count
from django.utils import translation, timezone
from rest_framework import viewsets, mixins, generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Category, Attribute, AttributeOption,
    Item, ItemPhoto, ItemAttributeValue, City,
    Conversation, Message, Notification, Favorite,
    IssueReport, Subscriber, PhoneVerificationCode, User
)
from .documents import ListingDocument
from .utils.sms import send_sms_code
from .utils.verification import send_code, verify_session_code

from .api_serializers import (
    UserPublicSerializer, UserProfileSerializer, ChangePasswordSerializer, RegisterSerializer,
    CategoryTreeSerializer, CategoryBriefSerializer, AttributeSerializer, AttributeOptionSerializer,
    CitySerializer,
    ItemListSerializer, ItemDetailSerializer, ItemCreateUpdateSerializer, ItemPhotoSerializer,
    FavoriteSerializer,
    ConversationSerializer, MessageSerializer, NotificationSerializer,
    IssueReportSerializer, SubscriberSerializer
)
from .api_permissions import IsOwnerOrReadOnly, IsConversationParticipant, IsMessageParticipant
from django.conf import settings
from .api_permissions import LoginRateThrottle  # add at the top with other imports
from rest_framework_simplejwt.exceptions import TokenError


# -------------------------
# Utils
# -------------------------
def jwt_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}

# -------------------------
# Auth
# -------------------------
class RegisterAPI(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        # send phone verification
        request = self.request
        send_code(request, user.phone, key_prefix="verify", purpose="verify", send_func=send_sms_code)

class LoginAPI(generics.GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail":"Invalid credentials."}, status=400)

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        data = {
            # keep old key name so existing frontends still work
            "token": str(access_token),
            # new: explicit refresh token
            "refresh": str(refresh),
            "user": UserProfileSerializer(user).data,
        }
        return Response(data)


class LogoutAPI(generics.GenericAPIView):
    """
    Logout by blacklisting the provided refresh token.
    Expecting JSON body: {"refresh": "<refresh_token>"}.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=400)

        try:
            token = RefreshToken(refresh_token)
            # blacklists the refresh token (requires token_blacklist app)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired refresh token."}, status=400)

        return Response({"detail": "Logged out successfully."})


class ProfileAPI(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class ChangePasswordAPI(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(ser.validated_data["old_password"]):
            return Response({"detail":"Old password incorrect."}, status=400)
        user.set_password(ser.validated_data["new_password"])
        user.save()
        return Response({"detail":"Password changed."})

# Phone code flows
class SendVerifyCodeAPI(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        send_code(request, request.user.phone, "verify", "verify", send_func=send_sms_code)
        return Response({"detail":"Code sent."})

class VerifyPhoneAPI(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        code = request.data.get("code", "")
        ok = verify_session_code(request, "verify", code)
        if not ok:
            return Response({"detail":"Invalid/expired code."}, status=400)
        return Response({"detail":"Phone verified."})

class ForgotPasswordAPI(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request):
        phone = (request.data.get("phone") or "").strip().replace(" ","")
        # Normalize like forms.py
        if phone.startswith("07") and len(phone)==10:
            phone = "962"+phone[1:]
        if not phone.startswith("9627") or len(phone)!=12:
            return Response({"detail":"Invalid phone."}, status=400)
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"detail":"No user with this phone."}, status=404)
        send_code(request, phone, "reset", "reset", send_func=send_sms_code)
        request.session["reset_phone"] = phone
        return Response({"detail":"Code sent."})

class VerifyResetCodeAPI(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request):
        code = request.data.get("code","")
        if not verify_session_code(request, "reset", code):
            return Response({"detail":"Invalid/expired code."}, status=400)
        request.session["reset_verified"] = True
        return Response({"detail":"Verified."})

class ResetPasswordAPI(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request):
        if not request.session.get("reset_verified"):
            return Response({"detail":"Not verified."}, status=400)
        phone = request.session.get("reset_phone")
        new_password = request.data.get("new_password")
        if not phone or not new_password:
            return Response({"detail":"Missing data."}, status=400)
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"detail":"User not found."}, status=404)
        user.set_password(new_password)
        user.save()
        # clear
        for key in ["reset_phone","reset_verified","reset_code","reset_sent_at"]:
            request.session.pop(key, None)
        return Response({"detail":"Password reset."})

# -------------------------
# Taxonomy
# -------------------------
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().select_related("parent").prefetch_related("subcategories","attributes")
    serializer_class = CategoryTreeSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=["get"])
    def attributes(self, request, pk=None):
        cat = self.get_object()
        data = Attribute.objects.filter(category=cat)
        return Response(AttributeSerializer(data, many=True).data)

class AttributeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Attribute.objects.all().prefetch_related("options")
    serializer_class = AttributeSerializer
    permission_classes = [AllowAny]

class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all().order_by("name_en")
    serializer_class = CitySerializer
    permission_classes = [AllowAny]

# -------------------------
# Items
# -------------------------
class ItemViewSet(viewsets.ModelViewSet):
    queryset = (
        Item.objects.filter(
    listing__is_active=True,
    listing__is_approved=True
)
        .select_related("category","user","city")
        .prefetch_related("photos","attribute_values")
        .order_by("-created_at")
    )
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["create","update","partial_update"]:
            return ItemCreateUpdateSerializer
        if self.action == "retrieve":
            return ItemDetailSerializer
        return ItemListSerializer

    def perform_create(self, serializer):
        serializer.context.update({"request": self.request})
        self.instance = serializer.save()

    def perform_update(self, serializer):
        serializer.context.update({"request": self.request})
        self.instance = serializer.save()

    def get_queryset(self):
        qs = super().get_queryset()
        # Filters: q, category_id, city_id, price range, condition
        q = self.request.query_params.get("q", "")
        category_id = self.request.query_params.get("category_id")
        city_id = self.request.query_params.get("city_id")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        condition = self.request.query_params.get("condition")

        if category_id:
            qs = qs.filter(category_id=category_id)
        if city_id:
            qs = qs.filter(city_id=city_id)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if condition:
            qs = qs.filter(condition=condition)

        if q and len(q) >= 2:
            # Try ES first if enabled
            try:
                if not settings.IS_RENDER and hasattr(ItemDocument, "search"):
                    s = ItemDocument.search().query("multi_match", query=q, fields=[
                        "title", "description", "category.name", "category.parent.name",
                        "city.name", "attributes.name", "attributes.value", "condition",
                    ]).sort("-created_at")
                    ids = [int(h.meta.id) for h in s[0:200]]  # cap
                    return qs.filter(id__in=ids)
            except Exception:
                pass
            # Fallback DB
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reactivate(self, request, pk=None):
        item = self.get_object()
        if item.user_id != request.user.user_id:
            return Response(status=403)
        item.is_active = True
        item.save()
        return Response({"detail":"Item reactivated."})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_sold(self, request, pk=None):
        item = self.get_object()
        if item.user_id != request.user.user_id:
            return Response(status=403)
        # set flag used in your web flows
        item.sold_on_site = True
        item.is_active = False
        item.save()
        return Response({"detail":"Marked as sold."})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        item = self.get_object()
        if item.user_id != request.user.user_id:
            return Response(status=403)
        item.cancel_reason = request.data.get("reason","")
        item.is_active = False
        item.save()
        return Response({"detail":"Item canceled."})

class MyItemsAPI(generics.ListAPIView):
    serializer_class = ItemListSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Item.objects.filter(user=self.request.user).select_related("category").prefetch_related("photos").order_by("-created_at")

class ItemPhotoDeleteAPI(generics.DestroyAPIView):
    serializer_class = ItemPhotoSerializer
    permission_classes = [IsAuthenticated]
    queryset = ItemPhoto.objects.all()

    def perform_destroy(self, instance):
        if instance.item.user_id != self.request.user.user_id:
            raise PermissionError("Not allowed")
        instance.delete()

# -------------------------
# Favorites
# -------------------------
class FavoriteViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related("item","item__category").prefetch_related("item__photos").order_by("-created_at")

    def create(self, request):
        item_id = request.data.get("item_id")
        if not item_id:
            return Response({"detail":"item_id is required"}, status=400)
        Favorite.objects.get_or_create(user=request.user, item_id=item_id)
        return Response({"detail":"Added to favorites."}, status=201)

    def destroy(self, request, pk=None):
        try:
            fav = Favorite.objects.get(id=pk, user=request.user)
        except Favorite.DoesNotExist:
            return Response(status=404)
        fav.delete()
        return Response(status=204)

# -------------------------
# Conversations & Messages
# -------------------------
class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        return Conversation.objects.filter(Q(buyer=u) | Q(seller=u)).select_related("item","buyer","seller").order_by("-updated_at")

    def create(self, request, *args, **kwargs):
        item_id = request.data.get("item_id")
        if not item_id:
            return Response({"detail":"item_id is required."}, status=400)
        item = Item.objects.filter(id=item_id, is_active=True).first()
        if not item:
            return Response({"detail":"Item not found/active."}, status=404)
        u = request.user
        if item.user_id == u.user_id:
            return Response({"detail":"Cannot start conversation with yourself."}, status=400)
        conv, created = Conversation.objects.get_or_create(item=item, buyer=u, seller=item.user)
        return Response(ConversationSerializer(conv).data, status=201 if created else 200)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        return Message.objects.filter(Q(conversation__buyer=u)|Q(conversation__seller=u)).select_related("sender","conversation").order_by("created_at")

    def create(self, request, *args, **kwargs):
        conv_id = request.data.get("conversation_id")
        text = (request.data.get("text") or "").strip()
        if not conv_id or not text:
            return Response({"detail":"conversation_id and text are required."}, status=400)
        try:
            c = Conversation.objects.select_related("buyer","seller").get(id=conv_id)
        except Conversation.DoesNotExist:
            return Response({"detail":"Conversation not found."}, status=404)
        u = request.user
        if u.user_id not in (c.buyer_id, c.seller_id):
            return Response(status=403)
        msg = Message.objects.create(conversation=c, sender=u, text=text)
        # update conversation updated_at
        c.save(update_fields=["updated_at"])
        # optional: create Notification for the other participant
        other_id = c.seller_id if u.user_id == c.buyer_id else c.buyer_id
        Notification.objects.create(user_id=other_id, message=f"New message on {c.item.title}")
        return Response(MessageSerializer(msg).data, status=201)

# -------------------------
# Notifications
# -------------------------
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        n = self.get_object()
        n.is_read = True
        n.save(update_fields=["is_read"])
        return Response({"detail":"Marked read."})

# -------------------------
# Misc
# -------------------------
class IssueReportAPI(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = IssueReportSerializer
    permission_classes = [IsAuthenticated]
    queryset = IssueReport.objects.all()

class SubscribeAPI(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriberSerializer
    permission_classes = [AllowAny]
    queryset = Subscriber.objects.all()
