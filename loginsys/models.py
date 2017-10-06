import random
import urllib.request

from PIL import Image
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django_ulogin.models import ULoginUser
from django_ulogin.signals import assign
from django.core.files.storage import default_storage

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

    # link_image = 'images/events_calendar/' + request.user.profile.organization.name + str(file)
    # with default_storage.open(link_image, 'wb+') as destination:
    #     for chunk in file.chunks():
    #         destination.write(chunk)
    # im = Image.open('media/' + link_image)
    # bg = Image.new("RGB", im.size, (255, 255, 255))
    # bg.paste(im, im)
    # bg.save('media/' + link_image)


    if kwargs['registered']:
        user.first_name = json['first_name']
        user.last_name = json['last_name']
        user.email = json['email']
        url_image = json['photo_big']
        link = 'images/users/'  + str(random.randint(0,1000)) + 'img_' + json['email']
        img = urllib.request.urlopen(url_image).read()
        f = default_storage.open(link, "wb+")
        f.write(img)
        f.close()
        user.profile.image = link
        user.save()


assign.connect(receiver=catch_ulogin_signal,
               sender=ULoginUser,
               dispatch_uid='customize.models')

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