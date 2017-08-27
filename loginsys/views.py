import random

from PIL import Image
from django.contrib import auth
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, render_to_response
from django.contrib.auth.forms import UserCreationForm

# Create your views here.
from django.template.context_processors import csrf
from loginsys.models import customUserCreationForm


def login(request):
    args = {}
    args.update(csrf(request))
    args['page_header'] = 'Аутентификация'
    if request.POST:
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            args['login_error'] = 'Пароль или имя пользователя введены не правильно'
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
    args['page_header'] = 'Регистрация'
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
        args['page_header'] = 'Редактирование ' + request.user.username
        args.update(csrf(request))
        args['user'] = request.user
        if request.POST:
            try:
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                for file in request.FILES.getlist('image'):
                    link_image = 'images/users/' + str(random.random()) + str(file)
                    with default_storage.open(link_image, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    img = Image.open('media/' + link_image)
                    img = img.convert('RGB')
                    img.save('media/' + link_image)
                user = request.user
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
    return render(request, 'loginsys/7a2ef10772f2.html')