# marketplace/forms.py
import re
from django import forms
from django.contrib.auth import get_user_model
from django.utils import translation
from .models import Item

from .widgets import MultipleFileInput  # your existing widget

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"id": "id_password"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"id": "id_password2"}), label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'phone', 'email']

    def clean_password(self):
        pwd = self.cleaned_data.get('password', '')
        # if len(pwd) < 8 or not re.fullmatch(r'[A-Za-z0-9]+', pwd):
        if len(pwd) < 8:
            raise forms.ValidationError("كلمة المرور يجب أن تتكون من 8 أحرف/أرقام على الأقل وتحتوي على أحرف أو أرقام فقط.")
        return pwd

    def clean_password2(self):
        pwd = self.cleaned_data.get('password')
        pwd2 = self.cleaned_data.get('password2')
        if pwd != pwd2:
            raise forms.ValidationError("كلمتا المرور غير متطابقتين.")
        return pwd2

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip().replace(' ', '')
        # Accept "07xxxxxxxx" (10 digits) OR "9627xxxxxxxxx" (12 digits)
        if re.fullmatch(r'07\d{8}', phone):
            # normalize to 9627xxxxxxxx
            phone = '962' + phone[1:]
        elif re.fullmatch(r'9627\d{8}', phone):
            # already normalized
            pass
        else:
            raise forms.ValidationError("رقم الهاتف يجب أن يبدأ بـ 07 ويتكون من 10 أرقام، وسيتم حفظه بصيغة 9627xxxxxxxx.")
        return phone


class ItemForm(forms.ModelForm):
    # ✅ real file field
    images = forms.CharField(
        widget=MultipleFileInput(attrs={'multiple': True}),
        required=False
    )

    # ✅ Used/New radio
    condition = forms.ChoiceField(
        choices=[('new', 'New'), ('used', 'Used')],
        widget=forms.RadioSelect,
        required=True
    )

    class Meta:
        model = Item
        fields = ['title', 'condition', 'price', 'description']  # ORDER MATTERS

    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)

        if category:
            for attribute in category.attributes.all():
                field_name = f"attribute_{attribute.id}"
                lang = translation.get_language()
                label = attribute.name_ar if lang == 'ar' else attribute.name_en

                if attribute.input_type == 'text':
                    self.fields[field_name] = forms.CharField(
                        required=attribute.is_required, label=label
                    )

                elif attribute.input_type == 'number':
                    self.fields[field_name] = forms.FloatField(
                        required=attribute.is_required, label=label
                    )



                elif attribute.input_type == 'select':

                    choices = [

                        (opt.id, opt.value_ar if lang == 'ar' else opt.value_en)

                        for opt in attribute.options.all()

                    ]

                    choices.append(('__other__', 'Other'))

                    self.fields[field_name] = forms.ChoiceField(

                        choices=choices,

                        required=attribute.is_required,

                        label=label

                    )

                    self.fields[f"{field_name}_other"] = forms.CharField(

                        required=False,

                        label=f"{label} (Other)"

                    )

    # ✅ prevents Django from throwing "No file submitted"
    def clean(self):
        cleaned_data = super().clean()
        # ignore missing images validation completely
        cleaned_data['images'] = self.files.getlist('images')
        return cleaned_data

    def clean_images(self):
        return self.files.getlist('images')