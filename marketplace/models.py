from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# -----------------------
# Custom User
# -----------------------
class UserManager(BaseUserManager):
    def create_user(self, phone, username, password=None, email=None):
        if not phone:
            raise ValueError("Users must have a phone number")
        user = self.model(phone=phone, username=username, email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, username, password, email=None):
        user = self.create_user(phone=phone, username=username, password=password, email=email)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    show_phone = models.BooleanField(
        default=True,
        help_text="If true, your phone number will be visible to other users."
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["phone"]

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.first_name or ''} {self.last_name or ''})".strip()


# -----------------------
# Categories and Attributes
# -----------------------
class Category(models.Model):
    name_en = models.CharField(max_length=255, unique=True)
    name_ar = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        from django.utils import translation
        lang = translation.get_language()
        return self.name_ar if lang == 'ar' else self.name_en

    class Meta:
        verbose_name_plural = "Categories"



class Attribute(models.Model):
    INPUT_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('select', 'Select'),
    ]
    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255)
    input_type = models.CharField(max_length=50, choices=INPUT_TYPE_CHOICES, default='text')
    is_required = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="attributes")

    def __str__(self):
        from django.utils import translation
        lang = translation.get_language()
        return self.name_ar if lang == 'ar' else self.name_en



class AttributeOption(models.Model):
    value_en = models.CharField(max_length=255)
    value_ar = models.CharField(max_length=255)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="options")

    def __str__(self):
        from django.utils import translation
        lang = translation.get_language()
        return self.value_ar if lang == 'ar' else self.value_en



# -----------------------
# Items and related tables
# -----------------------
class Item(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
    ]

    title = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    description = models.TextField(blank=True)
    price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='items')

    sold_on_site = models.BooleanField(null=True, blank=True)  # null = user didn’t answer yet
    cancel_reason = models.CharField(max_length=255, blank=True, null=True)

    # moderation/state
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # ✅ NEW
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used')

    def __str__(self):
        return self.title



class ItemPhoto(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='items/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.item.title}"


class ItemAttributeValue(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='attribute_values')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.attribute.name_en}/{self.attribute.name_ar}: {self.value}"

    # TODO: see why chatgpt changed it to this ?
    # def __str__(self):
    #     # safe label
    #     try:
    #         from django.utils import translation
    #         return f"{self.attribute.name_ar if translation.get_language() == 'ar' else self.attribute.name_en}: {self.value}"
    #     except Exception:
    #         return f"{self.attribute_id}: {self.value}"



class Conversation(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="conversations")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer_conversations")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller_conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation on {self.item.title} between {self.buyer} and {self.seller}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # 👈 add this field


    def __str__(self):
        return f"From {self.sender}: {self.body[:20]}"


class Notification(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    item = models.ForeignKey('Item', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.title}"


class City(models.Model):
    name_en = models.CharField(max_length=150, unique=True)
    name_ar = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ["name_en"]

    def __str__(self):
        from django.utils import translation
        lang = translation.get_language()
        return self.name_ar if lang == "ar" else self.name_en


# -----------------------
# Favorites (Wishlist)
# -----------------------
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "item")
        indexes = [
            models.Index(fields=["user", "item"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.item.title}"
