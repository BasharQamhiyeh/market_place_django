# marketplace/forms.py
import re
from django import forms
from django.contrib.auth import get_user_model
from django.utils import translation
from .models import Item, City
from django.forms import ClearableFileInput
from django.contrib.auth.forms import PasswordChangeForm


from .widgets import MultipleFileInput  # your existing widget

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": "id_password"})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": "id_password2"}),
        label="Confirm Password"
    )

    show_phone = forms.BooleanField(
        required=False,
        label="عرض رقم الهاتف للمستخدمين الآخرين",
        help_text="فعّل هذا الخيار إذا كنت تريد أن يظهر رقم هاتفك للمستخدمين الآخرين.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'phone', 'first_name', 'last_name', 'email', 'show_phone']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not re.match(r'^[A-Za-z]', username):
            raise forms.ValidationError("اسم المستخدم يجب أن يبدأ بحرف.")
        return username

    def clean_password(self):
        pwd = self.cleaned_data.get('password', '')
        if len(pwd) < 8:
            raise forms.ValidationError(
                "كلمة المرور يجب أن تتكون من 8 أحرف/أرقام على الأقل وتحتوي على أحرف أو أرقام فقط."
            )
        return pwd

    def clean_password2(self):
        pwd = self.cleaned_data.get('password')
        pwd2 = self.cleaned_data.get('password2')
        if pwd != pwd2:
            raise forms.ValidationError("كلمتا المرور غير متطابقتين.")
        return pwd2

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip().replace(' ', '')
        if re.fullmatch(r'07\d{8}', phone):
            phone = '962' + phone[1:]  # normalize 07xxxxxxxx to 9627xxxxxxxxx
        elif not re.fullmatch(r'9627\d{8}', phone):
            raise forms.ValidationError(
                "رقم الهاتف يجب أن يبدأ بـ 07 ويتكون من 10 أرقام، وسيتم حفظه بصيغة 9627xxxxxxxx."
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
                        initial=existing_attrs.get(attribute.id, "")
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
                        initial=current if selected_choice == '__other__' else ""
                    )

    def clean(self):
        cleaned = super().clean()
        cleaned['images'] = self.files.getlist('images')
        return cleaned

    def clean_images(self):
        return self.files.getlist('images')
