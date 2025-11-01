from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import Item, Category, ItemAttributeValue, Attribute, AttributeOption, ItemPhoto, User, IssueReport, City
from .forms import UserRegistrationForm, ItemForm
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from django.forms import ModelForm
from django.contrib import messages
from django.core.paginator import Paginator
from .documents import ItemDocument
from .models import Conversation, Message, Notification
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from .models import Favorite  # ensure Favorite is imported
from elasticsearch import Elasticsearch
from django.conf import settings
from elasticsearch.exceptions import ConnectionError
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q, Count
from collections import deque


# Registration
def register(request):
    """
    Step 1: Collect registration data, send code (no user yet).
    Step 2: Verify code and create user only after success.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Temporarily store the data, not saving user yet
            request.session['pending_user_data'] = form.cleaned_data

            # Send code to phone (simulated)
            phone = form.cleaned_data['phone']
            code = send_sms_code(phone, "verify")

            # Store code in session
            request.session['verification_code'] = code

            messages.info(request, "📱 تم إرسال رمز التحقق إلى رقم هاتفك (افتح وحدة التحكم لتراه في الوضع التجريبي).")
            return redirect('verify_phone')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


# Login
def user_login(request):
    if request.method == 'POST':
        identifier = request.POST['username'].strip()
        password = request.POST['password']

        # Normalize phones like registration
        if identifier.startswith("07") and len(identifier) == 10:
            identifier = "962" + identifier[1:]

        # Try login by USERNAME
        user = authenticate(request, username=identifier, password=password)

        # Try login by PHONE
        if not user:
            try:
                user_obj = User.objects.get(phone=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user:
            login(request, user)
            return redirect('item_list')

        return render(request, 'login.html', {'error': "بيانات تسجيل الدخول غير صحيحة"})

    return render(request, 'login.html')

# Logout
def user_logout(request):
    logout(request)
    return redirect('item_list')

# Anyone can view items
from marketplace.models import City  # adjust path if needed

def item_list(request):
    # ✅ Auto-expire old items
    Item.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=7),
        is_active=True
    ).update(is_active=False)

    q = request.GET.get("q", "").strip()

    # --- Filters ---
    category_id_single = request.GET.get("category")        # existing param
    category_ids_multi = request.GET.getlist("categories")  # NEW
    city_id = request.GET.get("city")                       # NEW
    min_price = request.GET.get("min_price")                # NEW
    max_price = request.GET.get("max_price")                # NEW

    base_qs = Item.objects.filter(is_approved=True, is_active=True)

    # ✅ Category filter (multi first, single fallback)
    selected_category = None
    if category_ids_multi:
        all_ids = []
        for cid in category_ids_multi:
            try:
                cat = Category.objects.get(id=cid)
                all_ids += _category_descendant_ids(cat)
            except Category.DoesNotExist:
                continue
        if all_ids:
            base_qs = base_qs.filter(category_id__in=all_ids)
    elif category_id_single:
        try:
            selected_category = Category.objects.get(id=category_id_single)
            ids = _category_descendant_ids(selected_category)
            base_qs = base_qs.filter(category_id__in=ids)
        except Category.DoesNotExist:
            selected_category = None

    # ✅ City filter
    if city_id:
        base_qs = base_qs.filter(city_id=city_id)

    # ✅ Price range
    if min_price:
        base_qs = base_qs.filter(price__gte=min_price)
    if max_price:
        base_qs = base_qs.filter(price__lte=max_price)

    # ✅ Search (Elasticsearch + fallback)
    if len(q) >= 2:
        try:
            search = (
                ItemDocument.search()
                .query(
                    "multi_match",
                    query=q,
                    fields=[
                        "title",
                        "description",
                        "category.name",
                        "category.parent.name",
                        "city.name",
                        "attributes.name",
                        "attributes.value",
                        "condition",
                    ],
                    fuzziness="AUTO",
                )
                .sort("-created_at")
            )
            hits = search.execute().hits
            hit_ids = [str(hit.meta.id) for hit in hits]

            queryset = list(
                base_qs.filter(id__in=hit_ids)
                .select_related("category", "city", "user")
                .prefetch_related("photos")
            )
            queryset.sort(key=lambda i: hit_ids.index(str(i.id)))
        except Exception as e:
            print("[WARN] Elasticsearch unavailable:", e)
            queryset = base_qs.filter(title__icontains=q).order_by("-created_at")
    else:
        queryset = base_qs.order_by("-created_at")

    if isinstance(queryset, list):
        ids = [obj.id for obj in queryset]
        queryset = Item.objects.filter(id__in=ids).order_by("-created_at")

    queryset = queryset.select_related("category", "user", "city").prefetch_related("photos")

    paginator = Paginator(queryset, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = (
        Category.objects.filter(parent__isnull=True)
        .annotate(
            total_items=Count("items", filter=Q(items__is_active=True, items__is_approved=True))
            + Count(
                "subcategories__items",
                filter=Q(
                    subcategories__items__is_active=True,
                    subcategories__items__is_approved=True,
                ),
            )
        )
        .filter(total_items__gt=0)
        .prefetch_related("subcategories")
        .distinct()
    )

    cities = City.objects.all().order_by("name_ar")

    selected_categories = request.GET.getlist("categories")  # ✅ new fix

    context = {
        "page_obj": page_obj,
        "q": q,
        "selected_category": selected_category,
        "categories": categories,
        "cities": cities,
        "selected_categories": selected_categories,  # ✅ added for template
    }

    return render(request, "item_list.html", context)



# Item details
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    attributes = item.attribute_values.all()
    similar_items = []

    # ✅ Try Elasticsearch-based "More Like This" search
    if not settings.IS_RENDER:
        try:
            es = Elasticsearch(settings.ELASTICSEARCH_DSL['default']['hosts'])
            query = {
                "query": {
                    "more_like_this": {
                        "fields": ["title", "description"],
                        "like": [{"_index": "items", "_id": item.id}],
                        "min_term_freq": 1,
                        "max_query_terms": 12
                    }
                },
                "size": 6
            }
            response = es.search(index="items", body=query)
            hits = response.get("hits", {}).get("hits", [])
            ids = [hit["_id"] for hit in hits]

            # ✅ Filter out inactive / unapproved items
            similar_items = (
                Item.objects.filter(id__in=ids, is_approved=True, is_active=True)
                .exclude(id=item.id)
                .order_by('-created_at')[:6]
            )

            # ✅ Fallback if ES returns no similar results
            if not similar_items.exists():
                similar_items = (
                    Item.objects.filter(
                        category=item.category,
                        is_approved=True,
                        is_active=True,
                    )
                    .exclude(id=item.id)
                    .order_by('-created_at')[:6]
                )

        except ConnectionError as e:
            print("[WARN] Elasticsearch unavailable:", e)
            # ✅ Fallback if ES server down
            similar_items = (
                Item.objects.filter(
                    category=item.category,
                    is_approved=True,
                    is_active=True,
                )
                .exclude(id=item.id)
                .order_by('-created_at')[:6]
            )
    else:
        # ✅ Render fallback when IS_RENDER=True (no ES on Render)
        similar_items = (
            Item.objects.filter(
                category=item.category,
                is_approved=True,
                is_active=True,
            )
            .exclude(id=item.id)
            .order_by('-created_at')[:6]
        )

    return render(request, 'item_detail.html', {
        'item': item,
        'attributes': attributes,
        'similar_items': similar_items,
    })



# Only logged-in users can post
@login_required
def item_create(request):
    categories = Category.objects.filter(parent__isnull=True).prefetch_related("subcategories")


    # POST takes priority so we don't lose the category on submit
    category_id = request.POST.get('category') or request.GET.get('category')
    selected_category = Category.objects.filter(id=category_id).first() if category_id else None

    if request.method == 'POST':
        # --- DEBUG: log inbound data ---
        print("=== DEBUG: item_create POST ===")
        print("selected_category_id:", category_id, " resolved:", selected_category)
        print("POST keys:", list(request.POST.keys()))
        print("FILES keys:", list(request.FILES.keys()))
        print("FILES images count:", len(request.FILES.getlist('images')))
        print("================================")

        form = ItemForm(request.POST, request.FILES, category=selected_category)

        # --- DEBUG: before validation, list dynamic fields present ---
        print("Form fields:", list(form.fields.keys()))

        if form.is_valid() and selected_category:
            print("=== DEBUG: form is valid ===")
            item = form.save(commit=False)
            item.category = selected_category
            item.user = request.user

            # ✅ mark item pending review
            item.is_approved = False
            item.is_active = True

            item.save()

            # Save images
            for img in request.FILES.getlist('images'):
                ItemPhoto.objects.create(item=item, image=img)

            # Save dynamic attributes (including Other)
            for key, value in request.POST.items():
                if key.startswith("attribute_") and not key.endswith("_other"):
                    try:
                        attr_id = int(key.split('_')[1])
                    except Exception:
                        continue
                    if value == '__other__':
                        value = request.POST.get(f"{key}_other", "").strip()
                    if value:
                        ItemAttributeValue.objects.create(
                            item=item,
                            attribute_id=attr_id,
                            value=value
                        )

            # ✅ Notify all admins
            for admin in User.objects.filter(is_staff=True):
                Notification.objects.create(
                    user=admin,
                    title="New item pending approval",
                    body=f"🕓 '{item.title}' was posted by {request.user.username} and is awaiting approval.",
                    item=item
                )

            Notification.objects.create(
                user=request.user,
                title="✅ إعلانك قيد المراجعة",
                body=f"تم استلام إعلانك '{item.title}' وهو الآن بانتظار موافقة الإدارة.",
                item=item
            )

            messages.success(request, "✅ Your ad was submitted (pending review).")
            return redirect('item_list')

        # --- DEBUG: surface errors ---
        print("=== DEBUG: form is INVALID ===")
        print("form.errors:", form.errors.as_data())
        print("non_field_errors:", form.non_field_errors())
        print("cleaned_data (partial):", getattr(form, 'cleaned_data', {}))
        print("FILES images count:", len(request.FILES.getlist('images')))

        # Render with an explicit debug panel
        return render(request, 'item_create.html', {
            'form': form,
            'categories': categories,
            'selected_category': selected_category,
            'debug_info': {
                'post_keys': list(request.POST.keys()),
                'files_keys': list(request.FILES.keys()),
                'images_count': len(request.FILES.getlist('images')),
                'form_fields': list(form.fields.keys()),
                'errors_html': form.errors.as_ul(),
                'non_field_errors_html': form.non_field_errors(),
            }
        })

    # GET
    form = ItemForm(category=selected_category)
    return render(request, 'item_create.html', {
        'form': form,
        'categories': categories,
        'selected_category': selected_category,
    })


@login_required
def item_edit(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    category = item.category  # same category, cannot change it

    # ---- Prefill initial dynamic attribute values ----
    initial = {
        f"attribute_{av.attribute.id}": av.value
        for av in item.attribute_values.all()
    }

    form = ItemForm(request.POST or None, request.FILES or None,
                    category=category, initial=initial, instance=item)

    if request.method == "POST" and form.is_valid():

        # Save base item fields
        item = form.save(commit=False)
        item.is_approved = False  # requires review again
        item.was_edited = True
        item.save()

        # Remove old attributes
        ItemAttributeValue.objects.filter(item=item).delete()

        # Save new dynamic attributes
        for key, val in request.POST.items():
            if key.startswith("attribute_") and not key.endswith("_other"):
                try:
                    attr_id = int(key.split("_")[1])
                except:
                    continue

                if val == "__other__":
                    val = request.POST.get(f"{key}_other", "").strip()

                if val:
                    ItemAttributeValue.objects.create(
                        item=item, attribute_id=attr_id, value=val
                    )

        # Append newly uploaded files
        for img in request.FILES.getlist("images"):
            ItemPhoto.objects.create(item=item, image=img)

        messages.success(request, "✅ تم حفظ التعديلات وإرسال الإعلان للمراجعة.")
        return redirect("item_detail", item_id=item.id)

    return render(request, "item_edit.html", {
        "form": form,
        "item": item,
        "category": category,
    })



# Category form (simple)
class CategoryForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label="Parent Category",
        help_text="Optional — leave blank if this is a top-level category.",
    )

    class Meta:
        model = Category
        fields = ['name_en', 'name_ar', 'description', 'parent']


@staff_member_required
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category}" created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()

    return render(request, 'category_create.html', {'form': form})


# Optional: list categories (for admins)
@staff_member_required
def category_list(request):
    # Fetch all top-level categories (parent=None)
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')

    return render(request, 'category_list.html', {
        'categories': categories,
    })

# Form to create a new attribute for a category
class AttributeForm(forms.ModelForm):
    class Meta:
        model = Attribute
        fields = ['name_en', 'name_ar', 'input_type', 'is_required']

@staff_member_required
def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    attributes = category.attributes.all()

    attribute_form = AttributeForm()
    option_form = AttributeOptionForm()

    # Handle adding a new attribute
    if request.method == 'POST' and 'add_attribute' in request.POST:
        attribute_form = AttributeForm(request.POST)
        if attribute_form.is_valid():
            attr = attribute_form.save(commit=False)
            attr.category = category  # auto assign
            attr.save()
            messages.success(request, f"Attribute '{str(attr)}' added successfully!")
            return redirect('category_detail', category_id=category.id)

    # Handle adding a new option
    if request.method == 'POST' and 'add_option' in request.POST:
        attribute_id = request.POST.get('attribute_id')
        value_en = request.POST.get('value_en')
        value_ar = request.POST.get('value_ar')

        if attribute_id and value_en and value_ar:
            attribute = get_object_or_404(Attribute, id=attribute_id)
            AttributeOption.objects.create(
                attribute=attribute,
                value_en=value_en,
                value_ar=value_ar
            )
            messages.success(request, f"Option added to {str(attribute)}!")
            return redirect('category_detail', category_id=category.id)
        else:
            messages.error(request, "Please enter both English and Arabic values.")

    return render(request, 'category_detail.html', {
        'category': category,
        'attributes': attributes,
        'attribute_form': attribute_form,
        'option_form': option_form,
    })



class AttributeOptionForm(forms.ModelForm):
    class Meta:
        model = AttributeOption
        fields = ['value_en', 'value_ar', 'attribute']


@login_required
def start_conversation(request, item_id):
    item = Item.objects.get(id=item_id)

    # seller = item's owner
    seller = item.user
    buyer = request.user

    if seller == buyer:
        return redirect('item_detail', item_id=item_id)

    # Check if a conversation already exists
    convo = Conversation.objects.filter(item=item, buyer=buyer, seller=seller).first()
    if convo:
        return redirect('chat_room', conversation_id=convo.id)

    # Create new conversation
    convo = Conversation.objects.create(item=item, buyer=buyer, seller=seller)
    return redirect('chat_room', conversation_id=convo.id)


@login_required
def chat_room(request, conversation_id):
    convo = get_object_or_404(Conversation, id=conversation_id)

    # ✅ Security check
    if request.user not in [convo.buyer, convo.seller]:
        return redirect('item_list')

    # ✅ Mark other user's messages as read
    Message.objects.filter(
        conversation=convo,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    # ✅ Handle message sending
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(conversation=convo, sender=request.user, body=body)
            # You could redirect to avoid resubmission
            return redirect('chat_room', conversation_id=conversation_id)

    # ✅ Load messages after marking read
    messages = convo.messages.order_by('created_at')

    return render(request, 'chat_room.html', {
        'conversation': convo,
        'messages': messages,
    })

@login_required
def user_inbox(request):
    convos = Conversation.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-created_at')

    return render(request, 'inbox.html', {
        'convos': convos
    })


@login_required
def item_edit(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if item.user != request.user:
        return HttpResponseForbidden("Not allowed")

    categories = Category.objects.filter(parent__isnull=True).prefetch_related("subcategories")

    category_id = request.POST.get('category') or request.GET.get('category')
    selected_category = Category.objects.filter(id=category_id).first() if category_id else item.category

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, category=selected_category, instance=item)

        if form.is_valid():
            item = form.save(commit=False)
            item.category = selected_category
            item.is_approved = False  # requires re-approval
            item.save()

            # Remove old attributes
            item.attribute_values.all().delete()

            # Save attributes again
            for key, value in request.POST.items():
                if key.startswith("attribute_") and not key.endswith("_other"):
                    try:
                        attr_id = int(key.split('_')[1])
                    except Exception:
                        continue

                    if value == "__other__":
                        value = request.POST.get(f"{key}_other", "").strip()

                    if value:
                        ItemAttributeValue.objects.create(item=item, attribute_id=attr_id, value=value)

            # Save new photos
            for img in request.FILES.getlist("images"):
                ItemPhoto.objects.create(item=item, image=img)

            return redirect("my_items")

        return render(request, "item_edit.html", {
            "form": form,
            "categories": categories,
            "selected_category": selected_category,
            "item": item
        })

    form = ItemForm(category=selected_category, instance=item)

    return render(request, "item_edit.html", {
        "form": form,
        "categories": categories,
        "selected_category": selected_category,
        "item": item
    })


@login_required
def user_profile(request, user_id):
    from django.db.models import Q
    User = get_user_model()

    seller = get_object_or_404(User, user_id=user_id)

    items = Item.objects.filter(
        user=seller,
        is_approved=True,
        is_active=True
    ).order_by('-created_at')

    return render(request, 'user_profile.html', {
        'seller': seller,
        'items': items,
    })


@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # mark unread as read
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications.html', {
        'notifications': notifications
    })


def my_items(request):
    items = (
        Item.objects
        .filter(user=request.user)
        .order_by('-created_at')
        .select_related('category')
        .prefetch_related('photos')
    )

    paginator = Paginator(items, 8)   # 8 per page (you can change)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'my_items.html', {
        'page_obj': page_obj
    })

@login_required
def reactivate_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    if not item.is_active:
        item.is_active = True
        item.save()
        messages.success(request, "✅ Your item is active again.")
    else:
        messages.info(request, "ℹ️ Item is already active.")
    return redirect('my_items')




@login_required
def delete_item_photo(request, photo_id):
    photo = get_object_or_404(ItemPhoto, id=photo_id)

    if photo.item.user != request.user:
        return HttpResponseForbidden("Not allowed")

    item_id = photo.item.id
    photo.image.delete(save=False)
    photo.delete()
    return redirect("item_edit", item_id=item_id)

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    item.delete()
    messages.success(request, "Item deleted successfully.")
    return redirect('my_items')


@login_required
def cancel_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)

    if request.method == "POST":
        sold = request.POST.get("sold_on_site")
        reason = request.POST.get("reason", "").strip()

        # Only deactivate, don't change approval status
        item.is_active = False
        item.cancel_reason = reason
        item.sold_on_site = (sold == "yes")
        item.save(update_fields=["is_active", "cancel_reason", "sold_on_site"])

        messages.success(request, "✅ Your ad has been canceled (still approved for future reactivation).")
        return redirect("my_items")

    return render(request, "cancel_item.html", {"item": item})



@login_required
@require_POST
def toggle_favorite(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    # Optional: prevent favoriting your own item
    if item.user == request.user:
        messages.info(request, "ℹ️ You cannot favorite your own item.")
        return redirect("item_detail", item_id=item.id)

    fav, created = Favorite.objects.get_or_create(user=request.user, item=item)
    if created:
        messages.success(request, "⭐ Added to your favorites.")
    else:
        fav.delete()
        messages.info(request, "✳️ Removed from your favorites.")

    # Redirect back to item page or favorites page if query param present
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(next_url)



@login_required
def my_favorites(request):
    fav_qs = (
        Favorite.objects
        .filter(user=request.user)
        .select_related("item", "item__user", "item__category")
        .prefetch_related("item__photos")
        .order_by("-created_at")
    )

    paginator = Paginator(fav_qs, 12)  # 12 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "my_favorites.html", {
        "page_obj": page_obj
    })

from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import UserProfileEditForm, UserPasswordChangeForm


@login_required
def edit_profile(request):
    """Allow user to edit their profile info (not username or phone)."""
    user = request.user
    if request.method == "POST":
        form = UserProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ تم تحديث معلوماتك بنجاح.")
            return redirect('user_profile', user.user_id)
        else:
            messages.error(request, "⚠️ يرجى تصحيح الأخطاء.")
    else:
        form = UserProfileEditForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form})


@login_required
def change_password(request):
    """Allow user to change password."""
    if request.method == "POST":
        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep logged in
            messages.success(request, "✅ تم تغيير كلمة المرور بنجاح.")
            return redirect('user_profile', request.user.user_id)
        else:
            messages.error(request, "⚠️ يرجى تصحيح الأخطاء.")
    else:
        form = UserPasswordChangeForm(user=request.user)

    return render(request, 'change_password.html', {'form': form})


@require_GET
def search_suggestions(request):
    query = request.GET.get("q", "").strip()
    suggestions = []

    if len(query) < 2:
        return JsonResponse({"results": []})

    try:
        # 1️⃣ Match categories and subcategories
        matched_categories = (
            Category.objects.filter(
                Q(name_ar__icontains=query) | Q(name_en__icontains=query)
            )
            .select_related("parent")
            .order_by("name_ar")[:8]
        )

        for cat in matched_categories:
            parent_label = cat.parent.name_ar if cat.parent else None
            suggestions.append({
                "type": "category",
                "name": cat.name_ar,
                "parent": parent_label,
                "category_id": cat.id,
            })

        # 2️⃣ Match top items
        matched_items = (
            Item.objects.filter(
                is_approved=True,
                is_active=True,
                title__icontains=query
            )
            .select_related("category")
            .order_by("-created_at")[:5]
        )

        for item in matched_items:
            parent_label = item.category.parent.name_ar if item.category.parent else None
            suggestions.append({
                "type": "item",
                "name": item.title,
                "category": item.category.name_ar,
                "parent": parent_label,
            })

    except Exception as e:
        print("[WARN] Suggestion fetch failed:", e)

    return JsonResponse({"results": suggestions})


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


from .models import PhoneVerificationCode
from .utils.sms import send_sms_code
from .forms import PhoneVerificationForm, ForgotPasswordForm, ResetPasswordForm
from django.contrib.auth.hashers import make_password

@login_required
def send_verification_code(request):
    """Send code after registration or from profile if not verified."""
    user = request.user
    code = send_sms_code(user.phone, "verify")
    PhoneVerificationCode.objects.create(user=user, code=code, purpose="verify")
    messages.info(request, "📱 تم إرسال رمز التحقق إلى رقم هاتفك (افتح وحدة التحكم لتراه في الوضع التجريبي).")
    return redirect('verify_phone')


def verify_phone(request):
    """
    Step 2: Verify the SMS code and create the user in DB.
    """
    pending_data = request.session.get('pending_user_data')
    sent_code = request.session.get('verification_code')

    if not pending_data or not sent_code:
        messages.error(request, "انتهت الجلسة. يرجى التسجيل مجددًا.")
        return redirect('register')

    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['code']
            print(f"[DEBUG]: entered_code = {entered_code}, sent_code = {sent_code}")
            if entered_code == sent_code:
                # ✅ Create the user now — only after correct verification
                user = User.objects.create_user(
                    username=pending_data['username'],
                    phone=pending_data['phone'],
                    email=pending_data.get('email'),
                    password=pending_data['password'],
                )
                user.first_name = pending_data.get('first_name', '')
                user.last_name = pending_data.get('last_name', '')
                user.show_phone = pending_data.get('show_phone', True)
                user.phone_verified = True
                user.is_active = True
                user.save()

                # Cleanup temporary data
                del request.session['pending_user_data']
                del request.session['verification_code']

                # Log the user in
                login(request, user)
                messages.success(request, "✅ تم التحقق من رقم الهاتف وإنشاء الحساب بنجاح!")
                return redirect('item_list')
            else:
                messages.error(request, "⚠️ الرمز غير صحيح.")
    else:
        form = PhoneVerificationForm()

    return render(request, 'verify_phone.html', {'form': form})




def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone'].strip()
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                messages.error(request, "رقم الهاتف غير موجود.")
                return redirect('forgot_password')

            code = send_sms_code(phone, "reset")
            PhoneVerificationCode.objects.create(user=user, code=code, purpose="reset")
            request.session['reset_phone'] = phone
            messages.info(request, "📱 تم إرسال رمز إعادة التعيين (افتح وحدة التحكم لتراه في الوضع التجريبي).")
            return redirect('reset_password')
    else:
        form = ForgotPasswordForm()
    return render(request, 'forgot_password.html', {'form': form})


def reset_password(request):
    phone = request.session.get('reset_phone')
    if not phone:
        return redirect('forgot_password')
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            new_pwd = form.cleaned_data['new_password']
            try:
                user = User.objects.get(phone=phone)
                record = PhoneVerificationCode.objects.filter(user=user, code=code, purpose="reset").last()
                if record and record.is_valid():
                    user.password = make_password(new_pwd)
                    user.save()
                    record.delete()
                    del request.session['reset_phone']
                    messages.success(request, "✅ تم تعيين كلمة مرور جديدة بنجاح. يمكنك تسجيل الدخول الآن.")
                    return redirect('user_login')
                messages.error(request, "⚠️ الرمز غير صالح أو منتهي الصلاحية.")
            except User.DoesNotExist:
                messages.error(request, "حدث خطأ.")
    else:
        form = ResetPasswordForm()
    return render(request, 'reset_password.html', {'form': form})

from .models import Subscriber

def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            Subscriber.objects.get_or_create(email=email)
            messages.success(request, "✅ Thank you for subscribing!")
    return redirect('home')


from django.shortcuts import render

def contact(request):
    return render(request, "contact.html")


@login_required
def report_issue(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == "POST":
        IssueReport.objects.create(user=request.user, item=item, message=request.POST["message"])
        messages.success(request, "✅ Thank you for reporting this issue.")
        return redirect("item_detail", item_id=item.id)
    return redirect("item_detail", item_id=item.id)
