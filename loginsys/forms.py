from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class customUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label="Ім'я", widget=forms.TextInput)
    last_name = forms.CharField(label='Прізвище', widget=forms.TextInput)
    email = forms.EmailField(label='email', widget=forms.EmailInput)

    class Meta:
        model = User
        fields = ('username', 'email','first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserEditForm(forms.Form):
    email = forms.EmailField(max_length=50, label='Email')
    first_name = forms.CharField(max_length=50, label='Ім\'я')
    last_name = forms.CharField(max_length=50, label='Прізвище')
    image = forms.ImageField(label='')

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'