import random
import urllib

from django.views.generic import FormView
from django_ulogin.models import ULoginUser
from django_ulogin.signals import assign
from django.contrib import auth
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect

# Create your views here.
from django.template.context_processors import csrf
from loginsys.forms import customUserCreationForm, UserEditForm


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
    add_event = request.GET.get('add_event', '-1')
    print(add_event)
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

class UserEditView(FormView):
    template_name = 'loginsys/edit_user.html'
    form_class = UserEditForm

    def get_context_data(self, **kwargs):
        context = super(UserEditView, self).get_context_data()
        context['organizations'] = self.request.user.profile.signed_organizations.all()
        context['page_header'] = 'Редагування ' + self.request.user.first_name
        context['user'] = self.request.user
        return context

    def get_initial(self):
        initial = super(UserEditView, self).get_initial()
        initial['first_name'] = self.request.user.first_name
        initial['last_name'] = self.request.user.last_name
        initial['email'] = self.request.user.email
        initial['image'] = self.request.user.profile.image
        return initial

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        user = self.request.user
        user.first_name = cleaned_data['first_name']
        user.last_name = cleaned_data['last_name']
        user.email = cleaned_data['email']
        user.profile.image = cleaned_data['image']
        user.save()
        return super(UserEditView, self).form_valid(form)


def key(request):
    return render(request, 'loginsys/96f3c45875e1.html')