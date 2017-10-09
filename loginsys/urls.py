from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from loginsys import views

app_name = 'loginsys'
urlpatterns = [
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^registration/$', views.registration, name='registration'),
    url(r'^edit_user/$', login_required(views.UserEditView.as_view(success_url='/auth/edit_user')), name='edit_user'),
]