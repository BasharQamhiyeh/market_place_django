from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import Item, Category, ItemAttributeValue, Attribute, AttributeOption, ItemPhoto, User
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

# Registration
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('item_list')
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
def item_list(request):
    # ----------------------------------------------
    # ✅ Auto-expire items older than 7 days
    # ----------------------------------------------
    Item.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=7),
        is_active=True
    ).update(is_active=False)

    # ----------------------------------------------
    # ✅ Search query
    # ----------------------------------------------
    q = request.GET.get("q", "").strip()

    # ----------------------------------------------
    # ✅ If searching (min 2 chars) → use ES
    # ----------------------------------------------
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
                        "attributes.name",
                        "attributes.value",
                        "condition",
                    ],
                    fuzziness="AUTO",
                )
                .sort("-created_at")
            )

            hit_ids = [hit.meta.id for hit in search]
            queryset = Item.objects.filter(
                id__in=hit_ids,
                is_approved=True,
                is_active=True,
            ).order_by("-created_at")

        except Exception:
            # 🚨 Elasticsearch offline fallback
            queryset = Item.objects.filter(
                is_approved=True,
                is_active=True,
                title__icontains=q,
            ).order_by("-created_at")

    # ----------------------------------------------
    # ✅ No search → show all approved & active
    # ----------------------------------------------
    else:
        queryset = Item.objects.filter(
            is_approved=True,
            is_active=True,
        ).order_by("-created_at")

    # ----------------------------------------------
    # ✅ Pagination
    # ----------------------------------------------
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ----------------------------------------------
    # ✅ Partial response for HTMX
    # ----------------------------------------------
    if request.headers.get("HX-Request"):
        return render(request, "partials/item_results.html", {
            "page_obj": page_obj,
            "q": q,
        })

    # ----------------------------------------------
    # ✅ Normal page
    # ----------------------------------------------
    return render(request, "item_list.html", {
        "page_obj": page_obj,
        "q": q,
    })

# Item details
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    attributes = item.attribute_values.select_related('attribute')

    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, item=item).exists()

    return render(request, 'item_detail.html', {
        'item': item,
        'attributes': attributes,
        'is_favorited': is_favorited,
    })


# Only logged-in users can post
@login_required
def item_create(request):
    categories = Category.objects.all()

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
    class Meta:
        model = Category
        fields = ['name_en', 'name_ar', 'description']

# Only staff (admin) can add categories
@staff_member_required
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'category_create.html', {'form': form})


# Optional: list categories (for admins)
@staff_member_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})

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

    categories = Category.objects.all()
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
    # Business rule: reactivation keeps is_approved as-is, flips is_active on.
    # If you want re-approval after edit, don’t change is_approved here.
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

        item.is_active = False
        item.is_approved = False
        item.sold_on_site = (sold == "yes")
        item.cancel_reason = reason
        item.save()

        messages.success(request, "✅ Your ad has been canceled.")
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
