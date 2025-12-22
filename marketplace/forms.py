from django.contrib.auth import get_user_model
from django.utils import translation
from django.forms import ClearableFileInput
from django.contrib.auth.forms import PasswordChangeForm

from .models import (
    City, Listing
)

from .validators import validate_no_links_or_html
import re
from django import forms
from django.utils.translation import gettext_lazy as _
User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    COUNTRY_CHOICES = [
        ('JO', 'Jordan (+962)'),
    ]

    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        label=_("Country"),
        initial='JO',
        disabled=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    phone = forms.CharField(
        label=_("Phone number"),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07xxxxxxxx'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": "id_password"}),
        label=_("Password")
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": "id_password2"}),
        label=_("Confirm Password")
    )

    show_phone = forms.BooleanField(
        required=False,
        label=_("Display phone number to other users"),
        help_text=_("Enable this option if you want your phone number to be visible to other users."),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'country', 'phone', 'first_name', 'last_name', 'email', 'show_phone']
        labels = {
            'username': _("Username"),
            'first_name': _("First name"),
            'last_name': _("Last name"),
            'email': _("Email"),
        }

    # -----------------------------
    # ✅ Validations (unchanged)
    # -----------------------------
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not re.match(r'^[A-Za-z]', username):
            raise forms.ValidationError(_("The username must begin with a letter."))
        return username

    def clean_password(self):
        pwd = self.cleaned_data.get('password', '')
        if len(pwd) < 8:
            raise forms.ValidationError(
                _("Password must be 8 characters long.")
            )
        return pwd

    def clean_password2(self):
        pwd = self.cleaned_data.get('password')
        pwd2 = self.cleaned_data.get('password2')
        if pwd != pwd2:
            raise forms.ValidationError(_("Two passwords must not match.."))
        return pwd2

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip().replace(' ', '')
        if re.fullmatch(r'07\d{8}', phone):
            # Normalize to full international format
            phone = '962' + phone[1:]
        elif not re.fullmatch(r'9627\d{8}', phone):
            raise forms.ValidationError(
                _("Phone number must begin with 07 and be 10 digits long. It will be saved in the format 9627xxxxxxxx.")
            )
        return phone


class SignupAfterOtpForm(forms.Form):
    first_name = forms.CharField(label=_("First name"), max_length=150)
    last_name = forms.CharField(label=_("Last name"), max_length=150)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Confirm Password"), widget=forms.PasswordInput)

    def clean_password(self):
        pwd = self.cleaned_data.get("password", "")
        if len(pwd) < 8:
            raise forms.ValidationError(_("Password must be 8 characters long."))
        # optional: only letters/numbers if you want same old rule
        # if not re.fullmatch(r"[A-Za-z0-9]+", pwd):
        #     raise forms.ValidationError(_("Password must contain only letters and numbers."))
        return pwd

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", _("Two passwords must match."))
        return cleaned


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'show_phone']
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'email': 'البريد الإلكتروني',
            'show_phone': 'عرض رقم الهاتف للمستخدمين الآخرين',
        }
        widgets = {
            'show_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Optional: just reuse Django's built-in PasswordChangeForm
class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="كلمة المرور الحالية",
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'})
    )
    new_password1 = forms.CharField(
        label="كلمة المرور الجديدة",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )
    new_password2 = forms.CharField(
        label="تأكيد كلمة المرور الجديدة",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class PhoneVerificationForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        label="رمز التحقق",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل الرمز المرسل'})
    )

class ForgotPasswordForm(forms.Form):
    phone = forms.CharField(
        label="رقم الهاتف",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07xxxxxxxx'})
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip().replace(' ', '')

        # Convert 07xxxxxxxx → 9627xxxxxxxx
        if phone.startswith('07') and len(phone) == 10:
            phone = '962' + phone[1:]
        elif not phone.startswith('9627') or len(phone) != 12:
            raise forms.ValidationError("⚠️ يرجى إدخال رقم هاتف صالح.")
        return phone

class ResetPasswordForm(forms.Form):
    # code = forms.CharField(
    #     max_length=6,
    #     label="رمز التحقق",
    #     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل الرمز'})
    # )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'كلمة المرور الجديدة'}),
        label="كلمة المرور الجديدة"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'تأكيد كلمة المرور'}),
        label="تأكيد كلمة المرور"
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") != cleaned.get("confirm_password"):
            raise forms.ValidationError("كلمتا المرور غير متطابقتين.")
        return cleaned


class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ["name_ar", "name_en", "is_active"]





# ============================================================
# MULTI-FILE INPUT WIDGET
# ============================================================

class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


# ============================================================
# BASE LISTING FORM  (shared by Item + Request)
# ============================================================

class ListingBaseForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "description", "category", "city"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        return validate_no_links_or_html(title)

    def clean_description(self):
        desc = self.cleaned_data.get("description", "")
        if desc:
            return validate_no_links_or_html(desc)
        return desc


# =========================================================================
# DYNAMIC ATTRIBUTE FIELD BUILDER (used by BOTH ItemForm & RequestForm)
# =========================================================================

def build_dynamic_attribute_fields(form, category, instance_attribute_values, is_request=False):
    """
    Builds dynamic form fields for all attributes of a category.
    - `is_request=False`  → attributes required normally (Item)
    - `is_request=True`   → attributes NOT required (Request)
    """

    if not category:
        return

    lang = translation.get_language()

    for attribute in category.attributes.all():
        field_name = f"attr_{attribute.id}"
        label = attribute.name_ar if lang == "ar" else attribute.name_en

        existing_value = instance_attribute_values.get(attribute.id, "")

        required = attribute.is_required if not is_request else False

        # -----------------------------------------------------
        # TEXT
        # -----------------------------------------------------
        if attribute.input_type == "text":
            form.fields[field_name] = forms.CharField(
                required=required,
                label=label,
                initial=existing_value,
                validators=[validate_no_links_or_html],
                widget=forms.TextInput(
                    attrs={
                        "class": "add-ad-input",
                        "placeholder": label,
                    }
                ),
            )
            continue

        # -----------------------------------------------------
        # NUMBER
        # -----------------------------------------------------
        if attribute.input_type == "number":
            initial = None
            if isinstance(existing_value, (int, float)):
                initial = existing_value
            else:
                try:
                    initial = float(existing_value)
                except Exception:
                    initial = None

            form.fields[field_name] = forms.FloatField(
                required=required,
                label=label,
                initial=initial,
                widget=forms.NumberInput(
                    attrs={
                        "class": "add-ad-input",
                        "step": "0.01",
                        "placeholder": label,
                    }
                ),
            )
            continue

        # -----------------------------------------------------
        # SELECT (dropdown/radio/checkbox/tags)
        # -----------------------------------------------------
        if attribute.input_type == "select":
            options = list(attribute.options.all())
            choices = [
                (
                    str(opt.id),
                    opt.value_ar if lang == "ar" else opt.value_en
                )
                for opt in options
            ]
            choices.append(("__other__", "أخرى"))

            # detect selected value
            selected_choice = None
            if existing_value:
                for opt in options:
                    if existing_value == opt.value_en or existing_value == opt.value_ar:
                        selected_choice = str(opt.id)
                        break
                if selected_choice is None:
                    selected_choice = "__other__"

            ui = attribute.ui_type

            # DROPDOWN
            if ui == "dropdown":
                form.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    required=required,
                    label=label,
                    initial=selected_choice,
                    widget=forms.Select(
                        attrs={
                            "class": "add-ad-select",
                        }
                    ),
                )

            # RADIO
            elif ui == "radio":
                form.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    required=required,
                    label=label,
                    initial=selected_choice,
                    widget=forms.RadioSelect(
                        attrs={
                            "class": "flex flex-wrap gap-3 text-sm",
                        }
                    ),
                )

            # CHECKBOXES
            elif ui == "checkbox":
                initial_list = existing_value.split(",") if existing_value else []
                form.fields[field_name] = forms.MultipleChoiceField(
                    choices=choices,
                    required=required,
                    initial=initial_list,
                    label=label,
                    widget=forms.CheckboxSelectMultiple(
                        attrs={
                            "class": "flex flex-wrap gap-3 text-sm",
                        }
                    ),
                )

            # TAGS / MULTI SELECT
            elif ui == "tags":
                initial_list = existing_value.split(",") if existing_value else []
                form.fields[field_name] = forms.MultipleChoiceField(
                    choices=choices,
                    required=required,
                    initial=initial_list,
                    label=label,
                    widget=forms.SelectMultiple(
                        attrs={
                            "class": "tag-select add-ad-select",
                        }
                    ),
                )

            # FALLBACK
            else:
                form.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    required=required,
                    label=label,
                    initial=selected_choice,
                    widget=forms.Select(
                        attrs={
                            "class": "add-ad-select",
                        }
                    ),
                )

            # OTHER FIELD
            form.fields[f"{field_name}_other"] = forms.CharField(
                required=False,
                label=f"{label} (أخرى)",
                initial=existing_value if selected_choice == "__other__" else "",
                validators=[validate_no_links_or_html],
                widget=forms.TextInput(
                    attrs={
                        "class": "add-ad-input",
                        "placeholder": f"{label} (أخرى)",
                    }
                ),
            )
            continue


# ============================================================
# ITEM FORM (Sell)
# ============================================================

class ItemForm(ListingBaseForm):
    images = forms.CharField(
        widget=MultipleFileInput(attrs={"multiple": True}),
        required=False
    )

    condition = forms.ChoiceField(
        choices=[('new', 'جديد'), ('used', 'مستعمل')],
        widget=forms.RadioSelect,
        required=True
    )

    price = forms.FloatField(required=True)

    class Meta(ListingBaseForm.Meta):
        model = Listing
        fields = ["title", "description", "category", "city"]

    def __init__(self, *args, **kwargs):
        category = kwargs.pop("category", None)
        listing_instance = kwargs.get("instance", None)

        super().__init__(*args, **kwargs)

        # Existing attribute values
        existing = {}
        if listing_instance and hasattr(listing_instance, "item"):
            for av in listing_instance.item.attribute_values.all():
                existing[av.attribute_id] = av.value

        build_dynamic_attribute_fields(self, category, existing, is_request=False)

    def clean_images(self):
        return self.files.getlist("images")


# ============================================================
# REQUEST FORM (Buy)
# ============================================================

# ============================================================
# REQUEST FORM (Buy Request)
# ============================================================

class RequestForm(ListingBaseForm):
    """
    Form for creating a Request (طلب شراء).
    Behaves like ItemForm, but:
    - no images
    - attributes are NOT required
    - has budget + condition_preference + show_phone
    """

    budget = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "add-ad-input",
                "placeholder": "الميزانية المتوقعة (اختياري)"
            }
        )
    )

    condition_preference = forms.ChoiceField(
        choices=[
            ("any", "أي حالة"),
            ("new", "جديد"),
            ("used", "مستعمل"),
        ],
        widget=forms.RadioSelect(attrs={"class": "flex gap-4"}),
        required=True,
        label="الحالة المطلوبة"
    )

    show_phone = forms.BooleanField(
        required=False,
        initial=True,
        label="إظهار رقم الهاتف في الطلب؟",
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-jordan"}
        )
    )

    class Meta(ListingBaseForm.Meta):
        model = Listing
        fields = ["title", "description", "category", "city"]

    def __init__(self, *args, **kwargs):
        category = kwargs.pop("category", None)
        listing_instance = kwargs.get("instance", None)

        super().__init__(*args, **kwargs)

        # Existing attribute values
        existing = {}
        if listing_instance and hasattr(listing_instance, "request"):
            for av in listing_instance.request.attribute_values.all():
                existing[av.attribute_id] = av.value

        # Build dynamic fields (attributes optional)
        build_dynamic_attribute_fields(
            self, category, existing, is_request=True
        )

