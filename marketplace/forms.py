from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.forms import ClearableFileInput
from django.contrib.auth.forms import PasswordChangeForm

from .models import (
    City, Listing, StoreReview
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
    CONDITION_CHOICES = (
        ("personal", _("Personal")),
        ("store", _("Store")),
    )

    first_name = forms.CharField(label=_("First name"), max_length=150)
    last_name = forms.CharField(label=_("Last name"), max_length=150)

    # from your hidden input: <input name="condition" ...>
    condition = forms.ChoiceField(
        label=_("Account type"),
        choices=CONDITION_CHOICES,
        required=False,          # default to personal if missing
    )

    # store fields (only required when condition == "store")
    store_name = forms.CharField(label=_("Store name"), max_length=255, required=False)
    store_logo = forms.ImageField(label=_("Store logo"), required=False)

    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Confirm Password"), widget=forms.PasswordInput)

    def clean_password(self):
        pwd = self.cleaned_data.get("password", "") or ""
        if len(pwd) < 8:
            raise forms.ValidationError(_("Password must be 8 characters long."))
        return pwd

    def clean(self):
        cleaned = super().clean()

        # passwords match
        p1 = cleaned.get("password")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", _("Two passwords must match."))

        # default condition if missing
        condition = cleaned.get("condition") or "personal"
        cleaned["condition"] = condition

        # store requirements
        if condition == "store":
            store_name = (cleaned.get("store_name") or "").strip()
            if not store_name:
                self.add_error("store_name", _("Store name is required for store accounts."))
        else:
            # ignore store fields for personal accounts
            cleaned["store_name"] = ""
            cleaned["store_logo"] = None

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
        fields = ["title", "description", "category", "city", "show_phone"]
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

from django import forms
from django.utils import translation

def build_dynamic_attribute_fields(form, category, instance_attribute_values, is_request=False):
    """
    Builds dynamic form fields for all attributes of a category.
    - is_request=False → attributes required normally (Item)
    - is_request=True  → attributes NOT required (Request)
    """
    if not category:
        return

    lang = translation.get_language()

    def _split_csv(v):
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            return [str(x).strip() for x in v if str(x).strip()]
        s = str(v).strip()
        if not s:
            return []
        return [p.strip() for p in s.split(",") if p.strip()]

    for attribute in category.attributes.all():
        field_name = f"attr_{attribute.id}"
        label = attribute.name_ar if lang == "ar" else attribute.name_en

        existing_value = instance_attribute_values.get(attribute.id, "")
        required = attribute.is_required if not is_request else False

        # -------------------------
        # TEXT
        # -------------------------
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

        # -------------------------
        # NUMBER
        # -------------------------
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

        # -------------------------
        # SELECT (dropdown/radio/checkbox/tags)
        # -------------------------
        if attribute.input_type == "select":
            options = list(attribute.options.all())

            # choices: option ids + sentinel "__other__"
            choices = [
                (str(opt.id), opt.value_ar if lang == "ar" else opt.value_en)
                for opt in options
            ]
            choices.append(("__other__", "أخرى"))

            option_ids = {str(opt.id) for opt in options}
            label_to_id = {}
            for opt in options:
                label_to_id[str(opt.value_ar)] = str(opt.id)
                label_to_id[str(opt.value_en)] = str(opt.id)

            ui = attribute.ui_type

            selected_choice = None
            other_text_initial = ""

            # ---- Single choice (dropdown/radio/fallback)
            if ui in ("dropdown", "radio") or ui not in ("checkbox", "tags"):
                ev = "" if existing_value is None else str(existing_value).strip()

                if ev:
                    # stored as option id
                    if ev in option_ids:
                        selected_choice = ev
                    # stored as label
                    elif ev in label_to_id:
                        selected_choice = label_to_id[ev]
                    # stored as free text -> other
                    else:
                        selected_choice = "__other__"
                        other_text_initial = ev

                # build field
                if ui == "dropdown":
                    form.fields[field_name] = forms.ChoiceField(
                        choices=choices,
                        required=required,
                        label=label,
                        initial=selected_choice,
                        widget=forms.Select(attrs={"class": "add-ad-select"}),
                    )
                elif ui == "radio":
                    form.fields[field_name] = forms.ChoiceField(
                        choices=choices,
                        required=required,
                        label=label,
                        initial=selected_choice,
                        widget=forms.RadioSelect(attrs={"class": "flex flex-wrap gap-3 text-sm"}),
                    )
                else:
                    form.fields[field_name] = forms.ChoiceField(
                        choices=choices,
                        required=required,
                        label=label,
                        initial=selected_choice,
                        widget=forms.Select(attrs={"class": "add-ad-select"}),
                    )

            # ---- Multi choice (checkbox/tags)
            else:
                parts = _split_csv(existing_value)
                initial_list = []
                for p in parts:
                    # stored as option id
                    if p in option_ids:
                        initial_list.append(p)
                        continue

                    # stored as label
                    if p in label_to_id:
                        initial_list.append(label_to_id[p])
                        continue

                    # free text -> other
                    if "__other__" not in initial_list:
                        initial_list.append("__other__")
                    other_text_initial = p  # last other wins

                widget = (
                    forms.CheckboxSelectMultiple(attrs={"class": "flex flex-wrap gap-3 text-sm"})
                    if ui == "checkbox"
                    else forms.SelectMultiple(attrs={"class": "tag-select add-ad-select"})
                )

                form.fields[field_name] = forms.MultipleChoiceField(
                    choices=choices,
                    required=required,
                    initial=initial_list,
                    label=label,
                    widget=widget,
                )

            # OTHER FIELD (always present)
            form.fields[f"{field_name}_other"] = forms.CharField(
                required=False,
                label=f"{label} (أخرى)",
                initial=other_text_initial,
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

from django import forms
from django.core.exceptions import ObjectDoesNotExist

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
        fields = ["title", "description", "category", "city", "show_phone"]

    def __init__(self, *args, **kwargs):
        category = kwargs.pop("category", None)
        listing_instance = kwargs.get("instance", None)

        super().__init__(*args, **kwargs)

        self._item = None
        if listing_instance:
            try:
                self._item = listing_instance.item
            except ObjectDoesNotExist:
                self._item = None

        if self._item:
            self.fields["price"].initial = self._item.price
            self.initial["price"] = self._item.price

            self.fields["condition"].initial = self._item.condition
            self.initial["condition"] = self._item.condition

        # Existing attribute values
        existing = {}
        if self._item:
            for av in self._item.attribute_values.all():
                existing[av.attribute_id] = av.value

        build_dynamic_attribute_fields(self, category, existing, is_request=False)

    def clean_images(self):
        return self.files.getlist("images")

    def clean(self):
        cleaned = super().clean()

        # -----------------------------------------
        # 1) "__other__" must have text in *_other
        # -----------------------------------------
        for name in list(self.fields.keys()):
            if not name.startswith("attr_") or name.endswith("_other"):
                continue

            other_name = f"{name}_other"
            if other_name not in self.fields:
                continue

            val = cleaned.get(name)
            other_val = (cleaned.get(other_name) or "").strip()

            other_selected = (
                val == "__other__"
                or (isinstance(val, (list, tuple)) and "__other__" in val)
            )

            if other_selected and not other_val:
                self.add_error(other_name, "الرجاء إدخال قيمة أخرى")

        # -----------------------------------------
        # 2) Photos validation (at least 1 photo)
        #    + validate main photo selection
        # -----------------------------------------
        new_images = self.files.getlist("images") or []
        new_count = len(new_images)

        # which existing photos will be deleted?
        deleted_ids = set()
        for key, v in self.data.items():
            if key.startswith("delete_photo_") and v:
                try:
                    deleted_ids.add(int(key.split("_")[-1]))
                except Exception:
                    pass

        remaining_existing = 0
        if self._item:
            qs = self._item.photos.all()
            if deleted_ids:
                qs = qs.exclude(id__in=deleted_ids)
            remaining_existing = qs.count()

        total_photos = remaining_existing + new_count
        if total_photos == 0:
            self.add_error("images", "الرجاء إضافة صور للإعلان")
            return cleaned  # no need to check main if no photos

        selected_main = (self.data.get("selected_main_photo") or "").strip()
        main_index = (self.data.get("main_photo_index") or "").strip()

        has_main_existing = False
        if selected_main.isdigit() and self._item:
            pid = int(selected_main)
            if pid not in deleted_ids:
                has_main_existing = self._item.photos.filter(id=pid).exclude(id__in=deleted_ids).exists()

        has_main_new = False
        if main_index.isdigit():
            idx = int(main_index)
            has_main_new = (0 <= idx < new_count)

        if not (has_main_existing or has_main_new):
            self.add_error("images", "الرجاء اختيار صورة رئيسية")
            self.add_error(None, "الرجاء اختيار صورة رئيسية")

        return cleaned



# ============================================================
# REQUEST FORM (Buy Request)
# ============================================================

class RequestForm(ListingBaseForm):
    budget = forms.DecimalField(
        required=True,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "add-ad-input", "placeholder": "الميزانية المتوقعة (اختياري)"})
    )

    condition_preference = forms.ChoiceField(
        choices=[("any", "أي حالة"), ("new", "جديد"), ("used", "مستعمل")],
        widget=forms.RadioSelect(attrs={"class": "flex gap-4"}),
        required=True,
        label="الحالة المطلوبة"
    )

    show_phone = forms.BooleanField(
        required=False,
        initial=True,
        label="إظهار رقم الهاتف في الطلب؟",
        widget=forms.CheckboxInput(attrs={"class": "h-4 w-4 text-jordan"})
    )

    # ✅ REQUIRED checkbox: backend must enforce it
    accept_terms = forms.BooleanField(required=True)

    class Meta(ListingBaseForm.Meta):
        model = Listing
        fields = ["title", "description", "category", "city"]

    def __init__(self, *args, **kwargs):
        category = kwargs.pop("category", None)
        listing_instance = kwargs.get("instance", None)
        super().__init__(*args, **kwargs)

        req = None
        if listing_instance:
            try:
                req = listing_instance.request
            except ObjectDoesNotExist:
                req = None

        if req:
            self.fields["budget"].initial = req.budget
            self.initial["budget"] = req.budget

            self.fields["condition_preference"].initial = req.condition_preference
            self.initial["condition_preference"] = req.condition_preference

        existing = {}
        if req:
            for av in req.attribute_values.all():
                existing[av.attribute_id] = av.value

        build_dynamic_attribute_fields(self, category, existing, is_request=True)

    def clean(self):
        cleaned = super().clean()

        # ✅ enforce "__other__" needs text (single + multi)
        for name, value in list(cleaned.items()):
            if not name.startswith("attr_"):
                continue
            if name.endswith("_other"):
                continue

            other_name = f"{name}_other"
            other_text = (cleaned.get(other_name) or "").strip()

            if isinstance(value, list):
                if "__other__" in value and not other_text:
                    self.add_error(other_name, "هذا الحقل مطلوب عند اختيار (أخرى).")
            else:
                if value == "__other__" and not other_text:
                    self.add_error(other_name, "هذا الحقل مطلوب عند اختيار (أخرى).")

        return cleaned


class StoreReviewForm(forms.ModelForm):
    class Meta:
        model = StoreReview
        fields = ["rating", "comment"]

