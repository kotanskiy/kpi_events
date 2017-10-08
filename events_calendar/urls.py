from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from events_calendar import views

app_name = 'calendar'
urlpatterns = [
    url(r'^$', views.EventsWithBaseFiltersListView.as_view(), name='home'),
    url(r'^organization_events/page/(\d+)$', views.organization_events),
    url(r'^event/(?P<pk>[\d+]*)$', views.EventDetailsView.as_view(), name='details'),
    url(r'^comments/(?P<event_id>[\d+]*)$', views.CommentsListView.as_view(), name='comments'),
    url(r'^add_comment/(?P<event_id>[\d+]*)$', views.add_comment, name='add_comment'),
    url(r'^organization_events$', views.organization_events, name='organization_events'),
    url(r'^organization_events/create_event', views.create_event, name='create_event'),
    url(r'^organization_events/edit_event/(?P<calendar_id>[\d+]*)$', views.edit_event, name='edit_event'),
    url(r'^organization_events/edit_organization$', views.edit_organization, name='edit_organization'),
    url(r'^subscribe$', views.subscribe, name='subscribe'),
    url(r'^my_feed$', login_required(views.EventsBySignedOrganizationsListView.as_view()), name='filter_by_signed_organizations'),
    url(r'^searching_results', views.searching_results, name='searching_results'),
    url(r'^searching_results/page/(\d+)$', views.searching_results),
    url(r'^suggest_an_event$', views.suggest_an_event, name='suggest_an_event'),
    url(r'^proposed_events$', views.proposed_events, name='proposed_events'),
    url(r'^proposed_events/page/(\d+)$', views.proposed_events),
    url(r'^edit_proposed_event/(?P<event_id>[\d+]*)$', views.edit_proposed_event, name='edit_proposed_event'),
    url(r'^unsubscribe$', views.unsubscribe, name='unsubscribe'),
    url(r'^filter_by_organization/(?P<organization_id>[\d+]*)$', views.EventsByOrganizationListView.as_view(), name='filter_by_organization'),
    url(r'^remove_proposed_event/(?P<event_id>[\d+]*)$', views.remove_proposed_event, name='remove_proposed_event'),
    url(r'^subscribe_on_organization$', views.subscribe_on_organization, name='subscribe_on_organization'),
]