from django.conf.urls import url

from loginsys import views

app_name = 'loginsys'
urlpatterns = [
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^registration/$', views.registration, name='registration'),
    url(r'^edit_user/$', views.edit_user, name='edit_user'),
]