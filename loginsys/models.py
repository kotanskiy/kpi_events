from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.forms import EmailField


#class customUserCreationForm(UserCreationForm):
#    first_name = forms.CharField(label='Имя', widget=forms.TextInput)
#    last_name = forms.CharField(label='Фамилия', widget=forms.TextInput)

from django_ulogin.models import ULoginUser
from django_ulogin.signals import assign

def catch_ulogin_signal(*args, **kwargs):
    """
    Обновляет модель пользователя: исправляет username, имя и фамилию на
    полученные от провайдера.

    В реальной жизни следует иметь в виду, что username должен быть уникальным,
    а в социальной сети может быть много "тёзок" и, как следствие,
    возможно нарушение уникальности.

    """
    user=kwargs['user']
    json=kwargs['ulogin_data']

    if kwargs['registered']:
        #user.username = json['nickname']
        user.first_name = json['first_name']
        user.last_name = json['last_name']
        user.email = json['email']
        user.save()


assign.connect(receiver=catch_ulogin_signal,
               sender=ULoginUser,
               dispatch_uid='customize.models')

class customUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label='Имя', widget=forms.TextInput)
    last_name = forms.CharField(label='Фамилия', widget=forms.TextInput)


    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user