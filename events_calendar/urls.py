from django.conf.urls import url
from django.views.static import serve

from events_calendar import views
from kpi_events import settings


app_name = 'calendar'
urlpatterns = [
    url(r'^$', views.calendar, name='home'),
    url(r'^event/(?P<calendar_id>[\d+]*)$', views.calendar_details, name='details'),
    url(r'^comments/(?P<calendar_id>[\d+]*)$', views.comments, name='comments'),
    url(r'^add_comment/(?P<calendar_id>[\d+]*)$', views.add_comment, name='add_comment'),
    url(r'^organization_events$', views.organization_events, name='organization_events'),
    url(r'^organization_events/create_event', views.create_event, name='create_event'),
    url(r'^organization_events/edit_event/(?P<calendar_id>[\d+]*)$', views.edit_event, name='edit_event'),
    url(r'^organization_events/edit_organization$', views.edit_organization, name='edit_organization'),
    url(r'^subscribe$', views.subscribe, name='subscribe'),
]