from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from events_calendar import views
from events_calendar.views import ProposeEventCreateView

app_name = 'calendar'
urlpatterns = [
    url(r'^$', views.EventsWithBaseFiltersListView.as_view(), name='home'),
    url(r'^event/(?P<pk>[\d+]*)$', views.EventDetailsView.as_view(), name='details'),
    url(r'^comments/(?P<event_id>[\d+]*)$', views.CommentsListView.as_view(), name='comments'),
    url(r'^add_comment/(?P<event_id>[\d+]*)$', views.add_comment, name='add_comment'),
    url(r'^organization_events$', login_required(views.AdminOrganizationEvents.as_view()), name='organization_events'),
    url(r'^organization_events/create_event$', login_required(views.EventCreateView.as_view(success_url='/organization_events')), name='create_event'),
    url(r'^organization_events/edit_event/(?P<pk>[\d+]*)$', login_required(views.EventEditView.as_view()), name='edit_event'),
    url(r'^organization_events/edit_organization/(?P<pk>[\d+]*)$', login_required(views.OrganizationEditView.as_view(success_url='/organization_events')), name='edit_organization'),
    url(r'^subscribe$', views.subscribe, name='subscribe'),
    url(r'^my_feed$', login_required(views.EventsBySignedEventsAndOrganizationsListView.as_view()), name='filter_by_signed_organizations'),
    url(r'^searching_results$', views.searching_results, name='searching_results'),
    url(r'^searching_results/page/(\d+)$', views.searching_results),
    url(r'^suggest_an_event$', login_required(ProposeEventCreateView.as_view(success_url='/')), name='suggest_an_event'),
    url(r'^proposed_events$', login_required(views.ProposedEventsListView.as_view()), name='proposed_events'),
    url(r'^edit_proposed_event/(?P<pk>[\d+]*)$', login_required(views.ProposeEventEditView.as_view(success_url='/proposed_events')), name='edit_proposed_event'),
    url(r'^unsubscribe$', views.unsubscribe, name='unsubscribe'),
    url(r'^remove_proposed_event/(?P<event_id>[\d+]*)$', views.remove_proposed_event, name='remove_proposed_event'),
    url(r'^subscribe_on_organization/(?P<organization_id>[\d+]*)$', views.subscribe_on_organization, name='subscribe_on_organization'),
    url(r'^insert_into_google_calendar$', views.auth_calendar_api, name='insert_into_google_calendar'),
    url(r'^oauth2callback$', views.auth_return),
    url(r'^(?P<organization_id>[^/]+)$', views.EventsByOrganizationListView.as_view(), name='filter_by_organization'),
]