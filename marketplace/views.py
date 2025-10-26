from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import Item, Category, ItemAttributeValue, Attribute, AttributeOption, ItemPhoto
from .forms import UserRegistrationForm, ItemForm
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from django.forms import ModelForm
from django.contrib import messages
from django.core.paginator import Paginator
from .documents import ItemDocument
from .models import Conversation, Message
from django.db.models import Q
from django.contrib.auth import get_user_model


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
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('item_list')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

# Logout
def user_logout(request):
    logout(request)
    return redirect('item_list')

# Anyone can view items
def item_list(request):
    from django.utils import timezone
    from datetime import timedelta

    # ✅ Auto-expire items older than 7 days
    Item.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=7),
        is_active=True
    ).update(is_active=False)

    q = request.GET.get('q', '')

    if q and len(q) >= 2:
        search = (
            ItemDocument
            .search()
            .query(
                "multi_match",
                query=q,
                fields=[
                    "title",
                    "description",
                    "category.name",
                    "attributes.name",
                    "attributes.value",
                ],
                fuzziness="AUTO",
            )
        )

        hit_ids = [hit.meta.id for hit in search]
        queryset = Item.objects.filter(
            id__in=hit_ids,
            is_approved=True,
            is_active=True
        ).order_by('-created_at')

    else:
        queryset = Item.objects.filter(
            is_approved=True,
            is_active=True
        ).order_by('-created_at')

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # ✅ HTMX partial request
    if request.headers.get('HX-Request'):
        return render(request, 'partials/item_results.html', {
            'page_obj': page_obj,
            'q': q,
        })

    # Normal request
    return render(request, 'item_list.html', {
        'page_obj': page_obj,
        'q': q,
    })

# Item details
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    attributes = item.attribute_values.select_related('attribute')
    return render(request, 'item_detail.html', {'item': item, 'attributes': attributes})

# Only logged-in users can post
@login_required
def item_create(request):
    categories = Category.objects.all()

    # Current category selected visually
    category_id = request.GET.get('category') or request.POST.get('category')
    selected_category = Category.objects.filter(id=category_id).first() if category_id else None

    if request.method == 'POST':
        # final submit
        form = ItemForm(request.POST, request.FILES, category=selected_category)

        if form.is_valid() and selected_category:
            item = form.save(commit=False)
            item.category = selected_category
            item.user = request.user
            item.save()

            for img in request.FILES.getlist('images'):
                ItemPhoto.objects.create(item=item, image=img)

            return redirect('item_list')

        # invalid form
        return render(request, 'item_create.html', {
            'form': form,
            'categories': categories,
            'selected_category': selected_category,
        })

    # GET request — show dynamic fields based on ?category=
    form = ItemForm(category=selected_category)

    return render(request, 'item_create.html', {
        'form': form,
        'categories': categories,
        'selected_category': selected_category,
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
    convo = Conversation.objects.get(id=conversation_id)

    # Security: Only buyer or seller can view
    if request.user not in [convo.buyer, convo.seller]:
        return redirect('item_list')

    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            Message.objects.create(conversation=convo, sender=request.user, body=body)

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

    # Security: Only the owner can edit
    if item.user != request.user:
        return redirect('item_detail', item_id=item_id)

    # Get category for dynamic attributes
    category = item.category

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, category=category, instance=item)

        if form.is_valid():
            edited_item = form.save(commit=False)

            # ✅ Require approval again
            edited_item.is_approved = False

            edited_item.save()

            # Save any new uploaded photos
            for img in request.FILES.getlist('images'):
                ItemPhoto.objects.create(item=item, image=img)

            messages.success(request, "Item updated. Pending admin approval.")
            return redirect('item_detail', item_id=item.id)

    else:
        form = ItemForm(category=category, instance=item)

    return render(request, 'item_edit.html', {
        'form': form,
        'item': item
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


