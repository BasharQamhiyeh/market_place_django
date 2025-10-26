from django import forms
from django.contrib.auth import get_user_model
from .models import Item, AttributeOption
from django.utils import translation
from .widgets import MultipleFileInput  # <-- import it


User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'phone', 'email']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords don't match.")
        return cd['password2']


from django import forms
from django.utils import translation
from .models import Item


from django import forms
from django.utils import translation
from .models import Item
from .widgets import MultipleFileInput

class ItemForm(forms.ModelForm):
    images = forms.CharField(
        widget=MultipleFileInput(attrs={'multiple': True}),
        required=False
    )

    class Meta:
        model = Item
        fields = ['title', 'description', 'price']  # do NOT add 'images'

    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)

        if category:
            for attribute in category.attributes.all():
                field_name = f"attribute_{attribute.id}"
                lang = translation.get_language()
                label = attribute.name_ar if lang == 'ar' else attribute.name_en

                if attribute.input_type == 'text':
                    self.fields[field_name] = forms.CharField(required=attribute.is_required, label=label)
                elif attribute.input_type == 'number':
                    self.fields[field_name] = forms.FloatField(required=attribute.is_required, label=label)
                elif attribute.input_type == 'select':
                    choices = [
                        (opt.id, opt.value_ar if lang == 'ar' else opt.value_en)
                        for opt in attribute.options.all()
                    ]
                    self.fields[field_name] = forms.ChoiceField(
                        choices=choices,
                        required=attribute.is_required,
                        label=label
                    )

    # ✅ Allow multiple files: return a list so validation passes
    def clean_images(self):
        return self.files.getlist('images')

