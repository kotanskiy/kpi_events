import random
import urllib

from django_ulogin.models import ULoginUser
from django_ulogin.signals import assign
from django.contrib import auth
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, render_to_response

# Create your views here.
from django.template.context_processors import csrf
from loginsys.forms import customUserCreationForm


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

def login(request):
    args = {}
    args.update(csrf(request))
    args['page_header'] = 'Аутентифікація'
    if request.POST:
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            args['login_error'] = "Пароль або ім'я користувача введені не правильно"
            return render(request, 'loginsys/login.html', args)

    else:
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'loginsys/login.html', args)


def logout(request):
    auth.logout(request)
    return redirect('/')

def registration(request):
    args = {}
    args['page_header'] = 'Реєстрація'
    args.update(csrf(request))
    args['form'] = customUserCreationForm()
    if request.POST:
        newuser_form = customUserCreationForm(request.POST)
        if newuser_form.is_valid():
            newuser_form.save()
            newuser = auth.authenticate(username=newuser_form.cleaned_data['username'], password=newuser_form.cleaned_data['password2'])
            auth.login(request, newuser)
            return redirect('/')
        else:
            args['form'] = newuser_form

    return render(request, 'loginsys/registration.html', args)


def edit_user(request):
    if request.user.username:
        signed_organizations = request.user.profile.signed_organizations.all()
        args = {}
        args['organizations'] = signed_organizations
        args['page_header'] = 'Редагування ' + request.user.first_name
        args.update(csrf(request))
        args['user'] = request.user
        if request.POST:
            try:
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                for file in request.FILES.getlist('image'):
                    link_image = 'images/users/' + str(random.random()) + str(file)
                    with default_storage.open(link_image, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                user = request.user
                if email.strip() != '':
                    user.email = email
                if first_name.strip() != '':
                    user.first_name = first_name
                if last_name.strip() != '':
                    user.last_name = last_name
                if link_image != '':
                    user.profile.image = link_image
                user.save()
            except UnboundLocalError:
                link_image = ''
                user = request.user
                if email.strip() != '':
                    user.email = email
                if first_name.strip() != '':
                    user.first_name = first_name
                if last_name.strip() != '':
                    user.last_name = last_name
                if link_image != '':
                    user.profile.image = link_image
                user.save()
        return render_to_response('loginsys/edit_user.html', args)
    else:
        return redirect('/')


def key(request):
    return render(request, 'loginsys/96f3c45875e1.html')