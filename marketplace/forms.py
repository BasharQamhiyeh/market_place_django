# marketplace/forms.py
import re
from django import forms
from django.contrib.auth import get_user_model
from django.utils import translation
from .models import Item, City
from django.forms import ClearableFileInput
from django.contrib.auth.forms import PasswordChangeForm
from .validators import validate_no_links_or_html



User = get_user_model()


import re
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import User


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


class ItemForm(forms.ModelForm):
    images = forms.CharField(
        widget=MultipleFileInput(attrs={'multiple': True}),
        required=False
    )

    condition = forms.ChoiceField(
        choices=[('new', 'New'), ('used', 'Used')],
        widget=forms.RadioSelect,
        required=True
    )

    city = forms.ModelChoiceField(
        queryset=City.objects.filter(is_active=True).order_by('name_en'),
        required=False,
        label="City"
    )

    class Meta:
        model = Item
        fields = ['title', 'condition', 'price', 'description', 'city']

    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # ✅ make city dropdown searchable
        self.fields['city'].widget.attrs.update({'class': 'searchable-select'})

        existing_attrs = {}
        if instance:
            for av in instance.attribute_values.all():
                existing_attrs[av.attribute.id] = av.value

        if category:
            for attribute in category.attributes.all():
                field_name = f"attribute_{attribute.id}"
                lang = translation.get_language()
                label = attribute.name_ar if lang == 'ar' else attribute.name_en

                # TEXT
                if attribute.input_type == 'text':
                    self.fields[field_name] = forms.CharField(
                        required=attribute.is_required,
                        label=label,
                        initial=existing_attrs.get(attribute.id, ""),
                        validators=[validate_no_links_or_html],
                    )

                # NUMBER
                elif attribute.input_type == 'number':
                    self.fields[field_name] = forms.FloatField(
                        required=attribute.is_required,
                        label=label,
                        initial=existing_attrs.get(attribute.id, "")
                    )

                # SELECT
                elif attribute.input_type == 'select':
                    choices = [
                        (opt.id, opt.value_ar if lang == 'ar' else opt.value_en)
                        for opt in attribute.options.all()
                    ]
                    choices.append(('__other__', 'Other'))

                    current = existing_attrs.get(attribute.id)
                    selected_choice = None

                    # Select match
                    for opt in attribute.options.all():
                        if opt.value_en == current or opt.value_ar == current:
                            selected_choice = opt.id

                    if selected_choice is None and current:
                        selected_choice = '__other__'

                    self.fields[field_name] = forms.ChoiceField(
                        choices=choices,
                        required=attribute.is_required,
                        label=label,
                        initial=selected_choice
                    )

                    # ✅ make attribute select searchable
                    self.fields[field_name].widget.attrs.update({'class': 'searchable-select'})

                    # Field for other (text)
                    self.fields[f"{field_name}_other"] = forms.CharField(
                        required=False,
                        label=f"{label} (Other)",
                        initial=current if selected_choice == '__other__' else "",
                        validators=[validate_no_links_or_html],
                    )

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        return validate_no_links_or_html(title)

    def clean_description(self):
        desc = self.cleaned_data.get("description", "")
        if desc is None:
            return desc
        return validate_no_links_or_html(desc)

    def clean(self):
        cleaned_data = super().clean()

        # Validate uploaded images
        files = self.files.getlist("images")

        MAX_MB = 5
        MAX_BYTES = MAX_MB * 1024 * 1024
        ALLOWED_EXTS = {"jpg", "jpeg", "png", "webp"}

        for f in files:
            if f.size > MAX_BYTES:
                self.add_error(
                    "images",
                    f"File {f.name} is too large (max {MAX_MB} MB).",
                )

            ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
            if ext not in ALLOWED_EXTS:
                self.add_error(
                    "images",
                    f"File {f.name} has an unsupported type. "
                    f"Allowed: {', '.join(sorted(ALLOWED_EXTS))}.",
                )

        return cleaned_data


    def clean_images(self):
        return self.files.getlist('images')


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